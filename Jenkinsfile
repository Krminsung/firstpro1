// Jenkinsfile

// 1. 젠킨스가 빌드/배포를 실행할 K8s Pod 템플릿 정의
podTemplate(
  cloud: 'kubernetes', 
  label: 'kaniko-builder', 
  serviceAccount: 'jenkins-admin', // K8s API 접근 권한 (Turn 94에서 만듦)
  containers: [
    // 컨테이너 1: Kaniko (Docker 빌드용, Docker 데몬 불필요)
    containerTemplate(
      name: 'kaniko', 
      image: 'gcr.io/kaniko-project/executor:debug', // 'debug' 이미지는 'cat' 명령어 등을 지원
      command: 'cat', 
      ttyEnabled: true
    ),
    // 컨테이너 2: Kubernetes 배포용
    containerTemplate(
      name: 'kubectl', 
      image: 'lachie/kubectl:v1.29', 
      command: 'cat', 
      ttyEnabled: true
    )
  ]) {
    
    // 'kaniko-builder' 라벨을 가진 Pod에서 아래 단계를 실행
    node('kaniko-builder') {
        def apiImageName = "ms9019/ha-pipeline-api:latest"
        def workerImageName = "ms9019/ha-pipeline-worker:latest"
        
        // --- 1단계: Git에서 코드 가져오기 ---
        stage('Checkout') {
            git 'https://github.com/Krminsung/firstpro1.git'
        }

        // --- 2단계: Docker Hub 인증 설정 (Kaniko용) ---
        // Kaniko는 '/kaniko/.docker/config.json' 파일에서 인증 정보를 읽음
        stage('Setup Docker Creds') {
            container('kaniko') {
                // (다음 단계에서 젠킨스에 'dockerhub-credentials'를 등록할 것입니다)
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh "echo '{\"auths\":{\"https://index.docker.io/v1/\":{\"username\":\"${DOCKER_USER}\",\"password\":\"${DOCKER_PASS}\",\"email\":\"not@used.com\"}}}' > /kaniko/.docker/config.json"
                }
            }
        }

        // --- 3단계: Kaniko로 이미지 빌드  & 푸시 ---

        stage('Build & Push Images') {
    container('kaniko') {
        // \`pwd\` 를 \\`pwd\\` 로 변경
        sh "/kaniko/executor --context \\`pwd\\` --dockerfile Dockerfile.api --destination ${apiImageName} --cache=true"

        // \`pwd\` 를 \\`pwd\\` 로 변경
        sh "/kaniko/executor --context \\`pwd\\` --dockerfile Dockerfile.worker --destination ${workerImageName} --cache=true"
    }
}
        
        // --- 4단계: Kubernetes에 배포 ---
        stage('Deploy') {
            container('kubectl') {
                // (이 'k8s/' 폴더와 YAML 파일들은 Day 2에 만들 것입니다)
                sh "kubectl apply -f k8s/"
            }
        }
    }
}