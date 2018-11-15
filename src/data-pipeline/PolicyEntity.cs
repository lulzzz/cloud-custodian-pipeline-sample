using System;
using Microsoft.WindowsAzure.Storage.Table;

namespace Microsoft.CloudCustodianPipelineSample
{
    /// <summary>
    /// An Azure Table storage entity that represents a resource returned by a Cloud Custodian policy
    /// The data is partitioned by policy name
    /// Records are uniquely identified by a combination of their resourceId and the date the policy was run
    /// </summary>
    public class ResourceEntity : TableEntity
    {
        public ResourceEntity(string subscriptionId, string policyName, DateTime date, string resourceId)
        {
            PartitionKey = policyName;
            // Slashes are not allowed in the PartitionKey or RowKey
            RowKey = $"{date.ToString("o")}{resourceId.Replace("/", ".")}";

            SubscriptionId = subscriptionId;
            Date = date;
            ResourceId = resourceId;
        }

        public string SubscriptionId { get; set; }
        public DateTime Date { get; set; }
        public string ResourceId { get; set; }
    }
}
