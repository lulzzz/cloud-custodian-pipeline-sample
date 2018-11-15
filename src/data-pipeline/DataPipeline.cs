using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.Azure.EventGrid.Models;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.EventGrid;
using Microsoft.Extensions.Logging;
using Microsoft.WindowsAzure.Storage;
using Microsoft.WindowsAzure.Storage.Blob;
using Microsoft.WindowsAzure.Storage.Table;
using Newtonsoft.Json.Linq;

namespace Microsoft.CloudCustodianPipelineSample
{
    public static class DataPipeline
    {
        private const string OutputTableName = "resources";

        [FunctionName("TransformCustodianLogs")]
        public static async Task TransformCustodianLogs([EventGridTrigger]EventGridEvent eventGridEvent, ILogger log)
        {
            log.LogInformation(eventGridEvent.Data.ToString());

            var connString = Environment.GetEnvironmentVariable("CustodianLogsStorage", EnvironmentVariableTarget.Process);
            if (!CloudStorageAccount.TryParse(connString, out var storageAccount))
                throw new Exception("Could not initialize a connection to CustodianLogsStorage");

            var blobUri = GetBlobUriFromEvent(eventGridEvent);
            var createdBlob = await StorageUtils.GetBlobAsync(storageAccount, blobUri);
            var contents = await StorageUtils.DecompressBlobContentsAsync(createdBlob);
            log.LogInformation($"Retrieved blob from {blobUri}");
            
            var results = BuildPolicyResults(createdBlob.Name, contents);
            await StorageUtils.UploadEntitiesAsync(storageAccount, OutputTableName, results);
            log.LogInformation($"Stored {results.Length} results in {storageAccount.TableEndpoint}{OutputTableName}");
        }

        private static Uri GetBlobUriFromEvent(EventGridEvent eventGridEvent)
        {
            var data = JToken.Parse(eventGridEvent.Data.ToString());
            var createdBlobUri = new Uri(data["url"].ToString());
            return createdBlobUri;
        }

        private static ResourceEntity[] BuildPolicyResults(string blobName, string json)
        {
            try
            {
                var resources = JArray.Parse(json);
                if (resources.Count == 0)
                    return new ResourceEntity[0];

                var match = Regex.Match(blobName, @"(?<subscriptionId>.*)/(?<policyName>.*)/(?<year>\d+)/(?<month>\d+)/(?<day>\d+)/(?<hour>\d+)/(.*).json.gz");
                var subscriptionId = match.Groups["subscriptionId"].Value;
                var policyName = match.Groups["policyName"].Value;

                var year = int.Parse(match.Groups["year"].Value);
                var month = int.Parse(match.Groups["month"].Value);
                var day = int.Parse(match.Groups["day"].Value);
                var hour = int.Parse(match.Groups["hour"].Value);
                var date = new DateTime(year, month, day, hour, 0, 0);

                return resources.Select(r => new ResourceEntity(
                    subscriptionId,
                    policyName,
                    date,
                    r["id"].ToString()
                )).ToArray();
            }
            catch (Exception e)
            {
                throw new Exception($"There was a problem parsing the Cloud Custodian resource results from blob: {blobName}", e);
            }
        }
    }
}
