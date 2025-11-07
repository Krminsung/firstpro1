// Jenkinsfile

// 1. 젠킨스가 빌드 작업을 실행할 K8s Pod 템플릿 정의
podTemplate(cloud: 'kubernetes', label: 'docker-builder', containers: [
    // Docker 이미지를 빌드하기 위한 'docker' 컨테이너
    containerTemplate(name: 'docker', image: 'docker:20.10.17', command: 'cat', ttyEnabled: true, privileged: true),
    // K8s에 배포하기 위한 'kubectl' 컨테이너
    containerTemplate(name: 'kubectl', image: 'lachie/kubectl:v1.29', command: 'cat', ttyEnabled: true)
  ]) {
    
    // 'docker-builder' 라벨을 가진 Pod에서 아래 단계를 실행
    node('docker-builder') {

        // --- Docker Hub 사용자 이름(ID) 설정 ---
        def apiImageName = "ms9019/ha-pipeline-api:latest"
        def workerImageName = "ms9019/ha-pipeline-worker:latest"
        
        
        // --- 1단계: Git에서 코드 가져오기 ---
        stage('Checkout') {
            // 이 Jenkinsfile이 포함된 Git 저장소를 체크아웃합니다.
            git 'https://github.com/Krminsung/firstpro1.git'
        }

        // --- 2단계: 도커 이미지 2개 빌드 ---
        stage('Build Images') {
            container('docker') {
                // Docker 소켓에 접근하기 위해 권한 설정 (Docker-in-Docker)
                sh 'chmod 666 /var/run/docker.sock'
                
                // Dockerfile.api로 API 이미지 빌드
                sh "docker build -f Dockerfile.api -t ${apiImageName} ."
                // Dockerfile.worker로 Worker 이미지 빌드
                sh "docker build -f Dockerfile.worker -t ${workerImageName} ."
            }
        }
        
        // --- 3단계: 도커 허브에 이미지 푸시 ---
        stage('Push Images') {
            container('docker') {
                // 젠킨스에 저장된 'dockerhub-credentials' 인증 정보를 사용
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh "echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin"
                    sh "docker push ${apiImageName}"
                    sh "docker push ${workerImageName}"
                }
            }
        }
        
        // --- 4단계: Kubernetes에 배포 ---
        stage('Deploy') {
            container('kubectl') {
                // (이 'k8s/' 폴더와 YAML 파일들은 다음 단계에서 만들 것입니다)
                sh "kubectl apply -f k8s/"
            }
        }
    }
}