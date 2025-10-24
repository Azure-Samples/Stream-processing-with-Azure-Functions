targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@metadata({
  azd: {
    type: 'location'
  }
})
param location string

metadata name = 'Event Hubs Demo'
metadata description = 'Creates Event Hubs triggered Azure Functions demo with Flex Consumption plan'

@description('Id of the user identity to be used for testing and debugging. This is not required in production. Leave empty if not needed.')
@metadata({
  azd: {
    type: 'principalId'
  }
})
param userPrincipalId string

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

var functionAppName = '${abbrs.webSitesFunctions}${resourceToken}'
var functionAppPlanName = '${abbrs.webServerFarms}${resourceToken}'
var functionAppIdentityName = '${abbrs.managedIdentityUserAssignedIdentities}${resourceToken}'
var resourceGroupName = '${abbrs.resourcesResourceGroups}${environmentName}'
var storageAccountName = '${abbrs.storageStorageAccounts}${resourceToken}'
var logAnalyticsName = '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
var appInsightsName = '${abbrs.insightsComponents}${resourceToken}'
var eventHubNamespaceName = '${abbrs.eventHubNamespaces}${resourceToken}'
var eventHubName = 'vehicle-events'

var deploymentStorageContainerName = 'app-package-${take(functionAppName, 32)}-${take(toLower(uniqueString(functionAppName, environmentName)), 7)}'
var storageBlobDataOwner = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
var storageQueueDataContributor = '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
var storageTableDataContributor = '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
var eventHubsDataReceiver = 'a638d3c7-ab3a-418d-83e6-5f17a39d4fde'
var eventHubsDataSender = '2b629674-e913-4c01-ae53-ef4638d8f975'
var MonitoringMetricsPublisherRoleId = '3913510d-42f4-4e42-8a64-420c390055eb'

// General resources
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.7.0' = {
  name: '${uniqueString(deployment().name, location)}-loganalytics'
  scope: resourceGroup
  params: {
    name: logAnalyticsName
    location: location
    tags: tags
    dataRetention: 30
  }
}

module monitoring 'br/public:avm/res/insights/component:0.4.1' = {
  name: '${uniqueString(deployment().name, location)}-appinsights'
  scope: resourceGroup
  params: {
    name: appInsightsName
    location: location
    tags: tags
    workspaceResourceId: logAnalytics.outputs.resourceId
    disableLocalAuth: true
    roleAssignments: [
      {
        roleDefinitionIdOrName: MonitoringMetricsPublisherRoleId
        principalId: funcUserAssignedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: MonitoringMetricsPublisherRoleId
        principalId: userPrincipalId
        principalType: 'User'
      }
    ]
  }
}

module eventHubNamespace 'br/public:avm/res/event-hub/namespace:0.12.5' = {
  scope: resourceGroup
  name: eventHubNamespaceName
  params: {
    name: eventHubNamespaceName
    location: location
    tags: tags
    skuName: 'Standard'
    disableLocalAuth: true
    eventhubs: [
      {
        name: eventHubName
        messageRetentionInDays: 1
        partitionCount: 32
      }
    ]
    roleAssignments:[
      {
        roleDefinitionIdOrName: eventHubsDataReceiver
        principalId: funcUserAssignedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: eventHubsDataSender
        principalId: userPrincipalId
        principalType: 'User'
      }
    ]
  }
}

module funcUserAssignedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: 'funcUserAssignedIdentity'
  scope: resourceGroup
  params: {
    location: location
    tags: tags
    name: functionAppIdentityName
  }
}

module storageAccount 'br/public:avm/res/storage/storage-account:0.13.2' = {
  scope: resourceGroup
  name: storageAccountName
  params: {
    name: storageAccountName
    location: location
    tags: tags
    skuName: 'Standard_LRS'
    kind: 'StorageV2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    } 
    minimumTlsVersion: 'TLS1_2'
    blobServices: {
      containers: [{name: deploymentStorageContainerName}]
    }
    roleAssignments:  [
      {
        roleDefinitionIdOrName: storageBlobDataOwner
        principalId: funcUserAssignedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: storageQueueDataContributor
        principalId: funcUserAssignedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: storageTableDataContributor
        principalId: funcUserAssignedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
      }
      {
        roleDefinitionIdOrName: storageBlobDataOwner
        principalId: userPrincipalId
        principalType: 'User'
      }
      {
        roleDefinitionIdOrName: storageQueueDataContributor
        principalId: userPrincipalId
        principalType: 'User'
      }
      {
        roleDefinitionIdOrName: storageTableDataContributor
        principalId: userPrincipalId
        principalType: 'User'
      }
    ]
  }
}

// Function App Plan (Flex Consumption)
module functionAppPlan 'br/public:avm/res/web/serverfarm:0.5.0' = {
  scope: resourceGroup
  name: functionAppPlanName
  params: {
    name: functionAppPlanName
    location: location
    tags: tags
    skuName: 'FC1'
    reserved: true
  }
}

// Function App
module functionApp 'br/public:avm/res/web/site:0.19.3' = {
  scope: resourceGroup
  name: functionAppName
  params: {
    name: functionAppName
    location: location
    tags: union(tags, { 'azd-service-name': 'function-app' })
    kind: 'functionapp,linux'
    serverFarmResourceId: functionAppPlan.outputs.resourceId
    httpsOnly: true
    managedIdentities: {
      userAssignedResourceIds: [
        '${funcUserAssignedIdentity.outputs.resourceId}'
      ]
    }
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storageAccount.outputs.primaryBlobEndpoint}${deploymentStorageContainerName}'
          authentication: {
            type: 'UserAssignedIdentity'
            userAssignedIdentityResourceId: funcUserAssignedIdentity.outputs.resourceId 
          }
        }
      }
      scaleAndConcurrency: {
        instanceMemoryMB: 2048
        maximumInstanceCount: 100
      }
      runtime: {
        name: 'dotnet-isolated'
        version: '8.0'
      }
    }
    siteConfig: {
      alwaysOn: false
    }
    configs: [{
      name: 'appsettings'
        properties: {
          AzureWebJobsStorage__credential: 'managedidentity'
          AzureWebJobsStorage__clientId: funcUserAssignedIdentity.outputs.clientId
          AzureWebJobsStorage__accountName: storageAccount.outputs.name
          APPLICATIONINSIGHTS_AUTHENTICATION_STRING: 'ClientId=${funcUserAssignedIdentity.outputs.clientId};Authorization=AAD'
          APPLICATIONINSIGHTS_CONNECTION_STRING: monitoring.outputs.connectionString
          EventHubConnection__fullyQualifiedNamespace: '${eventHubNamespace.name}.servicebus.windows.net'
          EventHubConnection__clientId : funcUserAssignedIdentity.outputs.clientId
          EventHubConnection__credential : 'managedidentity'
          EventHubName: eventHubName
          AZURE_CLIENT_ID: funcUserAssignedIdentity.outputs.clientId //Used by Open Telemetry managed identity
        }
    }]
  }
}


@description('The resource ID of the created Resource Group.')
output resourceGroupResourceId string = resourceGroup.id

@description('The name of the created Resource Group.')
output resourceGroupName string = resourceGroup.name

@description('The resource ID of the created Function App.')
output functionAppResourceId string = functionApp.outputs.resourceId

@description('The name of the created Function App.')
output functionAppName string = functionApp.outputs.name

@description('The resource ID of the created Event Hub Namespace.')
output eventHubNamespaceResourceId string = eventHubNamespace.outputs.resourceId

@description('The name of the created Event Hub.')
output eventHubName string = eventHubName

@description('The Event Hub namespace FQDN.')
output eventHubNamespaceFqdn string = '${eventHubNamespace.outputs.name}.servicebus.windows.net'
