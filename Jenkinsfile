// -*- mode: groovy -*-
// Jenkins on Kubernetes: Kaniko build + K8s rollout + RQ verification

pipeline {
  agent {
    kubernetes {
      label 'kaniko-builder'
      namespace 'jenkins'
      serviceAccount 'jenkins-admin'
      defaultContainer 'kubectl'
      yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: kaniko-builder
spec:
  restartPolicy: Never
  containers:
    - name: kaniko
      image: gcr.io/kaniko-project/executor:debug
      tty: true
      command: ['cat']
      resources:
        requests:
          memory: "512Mi"
        limits:
          memory: "1Gi"
      volumeMounts:
        # Docker registry 인증이 /kaniko/.docker/config.json 에 있다고 가정
        - name: docker-config
          mountPath: /kaniko/.docker/
    - name: kubectl
      image: bitnami/kubectl:latest
      tty: true
      command: ['sh', '-c', 'sleep 365d']
  volumes:
    - name: docker-config
      secret:
        secretName: docker-config   # <-- 레지스트리 시크릿 이름 (환경에 맞게 수정)
"""
    }
  }

  options {
    timestamps()
    ansiColor('xterm')
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 30, unit: 'MINUTES')
  }

  environment {
    NAMESPACE       = 'jenkins'
    DEPLOYMENT      = 'worker-deployment'
    CONTAINER_NAME  = 'worker-container'
    APP_LABEL       = 'ha-worker'

    IMAGE_REPO      = 'docker.io/ms9019/ha-pipeline-worker'
    // 태그는 빌드 번호 + 짧은 커밋 SHA 사용(없으면 빌드번호만)
    TAG             = "b${env.BUILD_NUMBER}"
  }

  stages {

    stage('Checkout') {
      steps {
        container('kubectl') {
          checkout scm
          script {
            // GIT_COMMIT이 있으면 TAG에 접미사를 더해준다
            if (env.GIT_COMMIT) {
              env.TAG = "b${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
            }
            echo "Final image tag: ${env.TAG}"
          }
        }
      }
    }

    stage('Build & Push (Kaniko)') {
      steps {
        container('kaniko') {
          sh """
            set -euo pipefail
            echo "[KANIKO] building ${IMAGE_REPO}:${TAG}"
            /kaniko/executor \
              --context `pwd` \
              --dockerfile `pwd`/Dockerfile \
              --destination ${IMAGE_REPO}:${TAG} \
              --single-snapshot \
              --cleanup \
              --verbosity info
          """
        }
      }
    }

    // === 배포 전: 이미지 내부에 rq가 들어있는지 1회성 파드로 검증 ===
    stage('Verify RQ in Image') {
      steps {
        container('kubectl') {
          sh """
            set -euo pipefail
            echo "[VERIFY-IMAGE] import rq in one-off pod"
            kubectl -n ${NAMESPACE} run rq-verify --image=${IMAGE_REPO}:${TAG} \
              --restart=Never --attach --rm --command -- \
              sh -lc 'python - <<PY
import sys
try:
    import rq
    print("RQ_OK", getattr(rq, "__version__", "unknown"))
    print("PY_OK", sys.version.split()[0])
except Exception as e:
    print("RQ_IMPORT_ERROR", e)
    raise
PY'
            echo "[VERIFY-IMAGE] OK"
          """
        }
      }
    }

    stage('Deploy to K8s') {
      steps {
        container('kubectl') {
          sh """
            set -euo pipefail
            echo "[DEPLOY] set image ${DEPLOYMENT}/${CONTAINER_NAME} -> ${IMAGE_REPO}:${TAG}"
            kubectl -n ${NAMESPACE} set image deployment/${DEPLOYMENT} \
              ${CONTAINER_NAME}=${IMAGE_REPO}:${TAG}
            echo "[DEPLOY] wait rollout"
            kubectl -n ${NAMESPACE} rollout status deployment/${DEPLOYMENT} --timeout=180s
          """
        }
      }
    }

    // === 배포 후: 실제 파드 안에서 rq import 되는지 재확인 ===
    stage('Verify RQ in Pod') {
      steps {
        container('kubectl') {
          sh """
            set -euo pipefail

            POD=\\$(kubectl -n ${NAMESPACE} get pods -l app=${APP_LABEL} \\
                  -o jsonpath='{.items[0].metadata.name}')
            echo "[VERIFY-POD] target pod: \\$POD"

            kubectl -n ${NAMESPACE} exec \\$POD -c ${CONTAINER_NAME} -- sh -lc '
              set -e
              echo "== python & pip =="
              which python; python -V
              which pip || true; pip -V || true

              echo "== rq import =="
              python - <<PY
import sys
try:
    import rq
    print("RQ_OK", getattr(rq, "__version__", "unknown"))
except Exception as e:
    print("RQ_IMPORT_ERROR", e); raise
PY
            '

            echo "[VERIFY-POD] OK"
          """
        }
      }
    }
  }

  post {
    failure {
      container('kubectl') {
        sh """
          set +e
          echo "==== DEBUG: events ===="
          kubectl -n ${NAMESPACE} get events --sort-by=.lastTimestamp | tail -n 50 || true
          echo "==== DEBUG: pod describe ===="
          POD=\\$(kubectl -n ${NAMESPACE} get pods -l app=${APP_LABEL} -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
          if [ -n "\\$POD" ]; then
            kubectl -n ${NAMESPACE} describe pod \\$POD || true
            echo "==== DEBUG: last logs (previous) ===="
            kubectl -n ${NAMESPACE} logs \\$POD -c ${CONTAINER_NAME} --previous --tail=200 || true
          fi
        """
      }
    }
    always {
      echo "Build: ${env.BUILD_TAG}, Image: ${IMAGE_REPO}:${TAG}"
    }
  }
}
