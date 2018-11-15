using System;
using System.IO;
using System.IO.Compression;
using System.Threading.Tasks;
using Microsoft.WindowsAzure.Storage;
using Microsoft.WindowsAzure.Storage.Blob;
using Microsoft.WindowsAzure.Storage.Table;

namespace Microsoft.CloudCustodianPipelineSample
{
    public static class StorageUtils
    {
        public static async Task<ICloudBlob> GetBlobAsync(CloudStorageAccount storageAccount, Uri createdBlobUri)
        {
            try
            {
                var blobClient = storageAccount.CreateCloudBlobClient();
                return await blobClient.GetBlobReferenceFromServerAsync(createdBlobUri);
            }
            catch (Exception e)
            {
                throw new Exception($"There was a problem accessing the blob: {createdBlobUri}", e);
            }
        }

        /// <summary>
        /// Retrieves a gzip'd blob and returns the decompressed contents as a string
        /// </summary>
        public static async Task<string> DecompressBlobContentsAsync(ICloudBlob blob)
        {
            try
            {
                using (var blobStream = new MemoryStream())
                {
                    await blob.DownloadToStreamAsync(blobStream);
                    blobStream.Position = 0;

                    using (var decompressionStream = new GZipStream(blobStream, CompressionMode.Decompress))
                    {
                        var streamReader = new StreamReader(decompressionStream);
                        return await streamReader.ReadToEndAsync();
                    }
                }
            }
            catch (Exception e)
            {
                throw new Exception($"There was a problem decompressing the blob: {blob.Uri}", e);
            }
        }

        public static async Task UploadEntitiesAsync(CloudStorageAccount storageAccount, string tableName, TableEntity[] results)
        {
            try
            {
                if (results.Length == 0)
                    return;

                var tableClient = storageAccount.CreateCloudTableClient();
                var table = tableClient.GetTableReference(tableName);
                await table.CreateIfNotExistsAsync();

                var batch = new TableBatchOperation();
                foreach(var entity in results)
                {
                    batch.InsertOrReplace(entity);
                }
                await table.ExecuteBatchAsync(batch);
            }
            catch (Exception e)
            {
                throw new Exception($"There was a problem adding data to the table: {tableName}", e);
            }
        }
    }
}
