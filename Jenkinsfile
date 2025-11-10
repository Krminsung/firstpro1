// Jenkinsfile (Scripted)

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
      image: 'alpine/k8s:1.29.15',
      command: 'cat',
      ttyEnabled: true
    )
  ]
) {
  node('kaniko-builder') {
    cleanWs()

    // 이미지 태그(필요 시 latest 대신 커밋 SHA 등으로 버저닝 권장)
    def apiImageName    = "ms9019/ha-pipeline-api:latest"
    def workerImageName = "ms9019/ha-pipeline-worker:latest"

    // --- 1) Git 체크아웃 ---
    stage('Checkout') {
      // 멀티브랜치 파이프라인이면 아래 한 줄이면 됩니다.
      checkout scm

      // 단일 파이프라인 잡이라면(멀티브랜치가 아니라면) 이 형태를 사용하세요:
      // git url: 'https://github.com/Krminsung/firstpro1.git', branch: 'main'
    }

    // --- 2) Docker Hub 인증 파일 생성 (Kaniko) ---
    stage('Setup Docker Creds') {
      container('kaniko') {
        withCredentials([usernamePassword(
          credentialsId: 'dockerhub-credentials',
          usernameVariable: 'DOCKER_USER',
          passwordVariable: 'DOCKER_PASS'
        )]) {
          // 디렉토리 보장
          sh '''
            set -eu
            mkdir -p /kaniko/.docker
            cat > /kaniko/.docker/config.json <<EOF
            {
              "auths": {
                "https://index.docker.io/v1/": {
                  "username": "${DOCKER_USER}",
                  "password": "${DOCKER_PASS}",
                  "email": "not@used.com"
                }
              }
            }
            EOF
          '''
        }
      }
    }

    // --- 3) Kaniko Build & Push ---
    stage('Build & Push Images') {
      container('kaniko') {
        // Kaniko 컨텍스트는 현재 워크스페이스로 지정
        // WORKSPACE는 Jenkins가 자동으로 설정하는 환경변수입니다.
        sh """
          /kaniko/executor \
            --context "${WORKSPACE}" \
            --dockerfile Dockerfile.api \
            --destination ${apiImageName} \
            --cache=true

          /kaniko/executor \
            --context "${WORKSPACE}" \
            --dockerfile Dockerfile.worker \
            --destination ${workerImageName} \
            --cache=true
        """
      }
    }

    // --- 4) 쿠버네티스 배포 ---
    stage('Deploy') {
      container('kubectl') {
        // 클러스터 내에서 ServiceAccount로 실행 중이므로 토큰/CA는 자동 마운트됨
        sh 'kubectl apply -f k8s/'
      }
    }
  }
}
