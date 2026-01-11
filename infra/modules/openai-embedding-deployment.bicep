// Module to deploy embedding model to existing Azure OpenAI resource
@description('Name of existing Azure OpenAI resource')
param openAIResourceName string

@description('Deployment name for the embedding model')
param embeddingDeploymentName string = 'text-embedding-3-small'

@description('Model capacity in thousands of tokens per minute')
param capacity int = 120

// Reference existing OpenAI resource
resource existingOpenAI 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: openAIResourceName
}

// Deploy embedding model
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: existingOpenAI
  name: embeddingDeploymentName
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
  }
  sku: {
    name: 'GlobalStandard'
    capacity: capacity
  }
}

output deploymentName string = embeddingDeployment.name
