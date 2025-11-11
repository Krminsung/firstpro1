// -*- mode: groovy -*-

// =================================================================
// == 1. 빌드 환경 정의 (K8s Agent Pod 템플릿)
// =================================================================
podTemplate(
  label: 'kaniko-builder',
  namespace: 'jenkins',
  serviceAccount: 'jenkins-admin', // (Turn 211: 권한 부여)
  volumes: [
    emptyDirVolume(mountPath: '/home/jenkins/agent', memory: false)
  ],
  containers: [
    // 컨테이너 1: Docker 이미지 빌드용 (Kaniko)
    containerTemplate(
      name: 'kaniko', 
      image: 'gcr.io/kaniko-project/executor:debug',
      command: 'cat',
      ttyEnabled: true,
      
      // --- ★★★ "올바른" 메모리 문법(Syntax)으로 수정 ★★★ ---
      resourceRequestMemory: "512Mi",
      resourceLimitMemory: "1Gi"
    ),
    // 컨테이너 2: Kubernetes 배포용 (kubectl)
    // (Turn 223 로그를 보니 bitnami:latest를 사용 중이셔서, 그것으로 반영했습니다.)
    containerTemplate(
      name: 'kubectl', 
      image: 'lachlanevenson/k8s-kubectl:v1.30.0', 
    //   command: '/bin/sh',
    //   args: '-c cat',
      command: 'cat',
      ttyEnabled: true,

      // --- ★★★ "올바른" 메모리 문법(Syntax)으로 수정 ★★★ ---
      resourceRequestMemory: "128Mi",
      resourceLimitMemory: "256Mi"
    )
  ]) { // node (Agent) 시작
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
        withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
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
