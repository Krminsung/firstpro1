// Jenkinsfile (Scripted) — API/WORKER 이미지를 Kaniko로 각각 빌드/푸시하고 set image로 배포

podTemplate(
  cloud: 'kubernetes',
  label: 'kaniko-builder',
  serviceAccount: 'jenkins-admin',
  containers: [
    containerTemplate(
      name: 'kaniko',
      image: 'gcr.io/kaniko-project/executor:debug',
      command: 'cat',
      ttyEnabled: true
    ),
    containerTemplate(
      name: 'kubectl',
      image: 'bitnami/kubectl:latest',
      command: 'cat',
      ttyEnabled: true
    )
  ],
  // 필요하다면 워크스페이스 퍼시스턴트볼륨 설정 추가
) {
  node('kaniko-builder') {
    // ===== 공통 ENV =====
    def REGISTRY = 'docker.io/ms9019'
    def API_IMG  = "${REGISTRY}/ha-pipeline-api"
    def WRK_IMG  = "${REGISTRY}/ha-pipeline-worker"
    def TAG      = env.BUILD_NUMBER  // 혹은 env.GIT_COMMIT.take(7)

    stage('Checkout') {
      checkout scm
    }

    // ===== DockerHub 로그인 (Kaniko용 config.json 생성) =====
    stage('Registry Login (kaniko auth)') {
      container('kaniko') {
        withCredentials([usernamePassword(credentialsId: 'DOCKERHUB_CRED', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
          sh '''
            mkdir -p /kaniko/.docker
            cat > /kaniko/.docker/config.json <<EOF
            {
              "auths": {
                "https://index.docker.io/v1/": {
                  "auth": "$(printf "%s:%s" "$DH_USER" "$DH_PASS" | base64)"
                }
              }
            }
            EOF
          '''
        }
      }
    }

    // ===== API 이미지 빌드/푸시 =====
    stage('Build & Push API') {
      container('kaniko') {
        sh """
          /kaniko/executor \
            --dockerfile=Dockerfile.api \
            --context=`pwd` \
            --destination=${API_IMG}:${TAG} \
            --cache=true
        """
      }
    }

    // ===== WORKER 이미지 빌드/푸시 =====
    stage('Build & Push Worker') {
      container('kaniko') {
        sh """
          /kaniko/executor \
            --dockerfile=Dockerfile.worker \
            --context=`pwd` \
            --destination=${WRK_IMG}:${TAG} \
            --cache=true
        """
      }
    }

    // ===== 쿠버네티스 배포 (이미지 태그 교체) =====
    stage('Deploy') {
      container('kubectl') {
        sh """
          kubectl -n jenkins set image deploy/api-deployment    api-container=${API_IMG}:${TAG}
          kubectl -n jenkins set image deploy/worker-deployment worker-container=${WRK_IMG}:${TAG}

          kubectl -n jenkins rollout status deploy/api-deployment
          kubectl -n jenkins rollout status deploy/worker-deployment
        """
      }
    }

    // (선택) 검증
    stage('Verify') {
      container('kubectl') {
        sh """
          kubectl get pods -n jenkins -l app=ha-worker -o jsonpath='{range .items[*]}{.metadata.name}{"\\t"}{.spec.containers[0].image}{"\\t"}{.status.containerStatuses[0].imageID}{"\\n"}{end}'
          kubectl logs -n jenkins -l app=ha-worker -c worker-container --tail=100 || true
        """
      }
    }
  }
}
