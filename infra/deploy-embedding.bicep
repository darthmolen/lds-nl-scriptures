// Main deployment file for embedding model
targetScope = 'resourceGroup'

@description('Name of existing Azure OpenAI resource')
param openAIResourceName string

@description('Deployment name for embedding model')
param embeddingDeploymentName string = 'text-embedding-3-small'

module embeddingDeployment 'modules/openai-embedding-deployment.bicep' = {
  name: 'embedding-deployment'
  params: {
    openAIResourceName: openAIResourceName
    embeddingDeploymentName: embeddingDeploymentName
  }
}

output embeddingDeploymentName string = embeddingDeployment.outputs.deploymentName
