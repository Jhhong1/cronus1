def APP
def IMAGE
pipeline{
    agent any
    stages{
        stage("Clone"){
            steps{
                script {
                    APP = checkout scm
                }
            }
        }
        stage("Build"){
            steps{
                script {
                    IMAGE = docker.build("cronus:${env.GIT_COMMIT}")
                }
            }
        }
        stage("Test"){
            steps{
                script {
                    IMAGE.withRun() { c->
                        sh "docker exec -t ${c.id} pytest"
                        sh "rm -rf reports"
                        sh "docker cp ${c.id}:/cronus/reports/ ${WORKSPACE}/reports/"
                    }
                }
            }
            post{
                always{
                    sh "tar -zcf report.tar.gz reports/"
                    archiveArtifacts 'report.tar.gz'
                    junit "reports/report.xml"
                }
            }
        }
    }
}