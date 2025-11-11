// -*- mode: groovy -*-

// =================================================================
// == 1. 빌드 환경 정의 (K8s Agent Pod 템플릿)
// =================================================================
podTemplate(
  label: 'kaniko-builder',
  namespace: 'jenkins',
  
  // (Turn 240/242) "권한 부족" (CrashLoopBackOff) 해결
  serviceAccount: 'jenkins-admin', 
  
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
      
      // (Turn 235) "exit code -2" (메모리 부족) 해결
      resourceRequestMemory: "512Mi", 
      resourceLimitMemory: "1Gi"
    ),
    // 컨테이너 2: Kubernetes 배포용 (kubectl)
    containerTemplate(
      name: 'kubectl', 
      image: 'bitnami/kubectl:latest', // (Turn 223 로그 기준)
      command: 'cat',
      ttyEnabled: true,
      
      // (Turn 235) "exit code -2" (메모리 부족) 해결
      resourceRequestMemory: "128Mi",
      resourceLimitMemory: "256Mi"
    )
  ]) { // "podTemplate" 괄호 시작

    // =================================================================
    // == 2. 파이프라인 변수 정의
    // =================================================================
    node('kaniko-builder') { // "node" 괄호 시작

        // (Turn 153) "Stale Cache" (유령 캐시) 해결
        cleanWs() 

        def API_IMG = "docker.io/ms9019/ha-pipeline-api"
        def WRK_IMG = "docker.io/ms9019/ha-pipeline-worker"
        def TAG = "${env.BUILD_NUMBER}" // 이미지 태그 (예: 42)

        // =================================================================
        // == 3. 파이프라인 스테이지 (CI/CD)
        // =================================================================
        
        // --- 1단계: Git에서 코드 가져오기 ---
        stage('Checkout') {
            // (Turn 156) 젠킨스 UI의 Git 설정(ID, Branch)을 그대로 사용
            checkout scm 
        }

        // --- 2단계: Docker Hub 로그인 설정 (Kaniko용) ---
        stage('Registry Login (kaniko auth)') {
            container('kaniko') {
                withCredentials([usernamePassword(
                    // (Turn 215) 젠킨스에 등록된 ID로 수정
                    credentialsId: 'dockerhub-credentials', 
                    passwordVariable: 'DH_PASS',
                    usernameVariable: 'DH_USER'
                )]) {
                    sh """
                    set -eu
                    mkdir -p /kaniko/.docker
                    # Kaniko v1.9.0+ 방식 (base64)
                    AUTH=\$(printf '%s:%s' "\$DH_USER" "\$DH_PASS" | base64)
                    cat > /kaniko/.docker/config.json <<EOF
                    {
                        "auths": {
                            "https://index.docker.io/v1/": {
                                "auth": "\$AUTH"
                            }
                        }
                    }
                    EOF
                    """
                }
            }
        }

        // --- 3-1단계: API 이미지 빌드 & 푸시 (Kaniko) ---
        stage('Build & Push API') {
            container('kaniko') {
                sh """
                  set -euo pipefail
                  # (Turn 237) "Kaniko 오타" 수정
                  /kaniko/executor --dockerfile=Dockerfile.api \\
                                   --context=\`pwd\` \\
                                   --destination=\$API_IMG:\$TAG \\
                                   --cache=false 
                """
            }
        }
        
        // --- 3-2단계: Worker 이미지 빌드 & 푸시 (Kaniko) ---
        stage('Build & Push Worker') {
            container('kaniko') {
                sh """
                  set -euo pipefail
                  # (Turn 237) "Kaniko 오타" 수정
                  /kaniko/executor --dockerfile=Dockerfile.worker \\
                                   --context=\`pwd\` \\
                                   --destination=\$WRK_IMG:\$TAG \\
                                   --cache=false
                """
            }
        }

        // --- 4단계: K8s 클러스터에 배포 (Deploy) ---
        stage('Deploy') {
            container('kubectl') {
                sh """
                  set -euo pipefail
                  NS=jenkins
                  
                  # ★★★ (Turn 246) "set image" (가짜 치료) 대신 "apply -f" (진짜 치료) 실행 ★★★
                  # "k8s/" 폴더의 "모든" YAML (serviceAccountName, command 수정본)을 "적용(Apply)"
                  kubectl -n "\$NS" apply -f k8s/

                  # (젠킨스 UI에 로그를 남기기 위해 'set image'를 "추가"하되, "apply"가 메인)
                  kubectl -n "\$NS" set image deploy/api-deployment api-container=\$API_IMG:\$TAG
                  kubectl -n "\$NS" set image deploy/worker-deployment worker-container=\$WRK_IMG:\$TAG

                  # "롤링 업데이트"가 완료될 때까지 기다림
                  kubectl -n "\$NS" rollout status deployment/api-deployment --timeout=120s
                  kubectl -n "\$NS" rollout status deployment/worker-deployment --timeout=120s
                """
            }
        }

    } // "node" 괄호 끝
} // "podTemplate" 괄호 끝