# Information Retrieval

Download **Main Reports** and **County Fact Sheets** from here [https://www.knbs.or.ke/reports/kdhs-2022/
](https://www.knbs.or.ke/reports/kdhs-2022/)

Store the files here in your repository: **data/public_health_reports**

You can verify that Elasticsearch is running by opening your web browser and navigating to http://localhost:9200. You should see a JSON response containing information about your Elasticsearch node.

Elasticsearch: http://localhost:9200
Kibana: http://localhost:5601

### 5.2 Create an Index (without the attachment field in the mapping)

You only need to define mappings for other fields you want to explicitly control, such as filename. The content extracted by the attachment processor will be automatically detected and indexed.

```bash
curl -XPUT 'localhost:9200/public_health_index?pretty' -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "filename": { "type": "keyword" },
      "data": { "type": "binary" }
    }
  }
}
'
```

This creates an Elasticsearch index based on the name of the file as well as its content in raw binary format.
This is done in preparation for further processing and search.

* **curl -XPUT 'localhost:9200/public_health_index?pretty'**: Sends a **PUT** request to Elasticsearch running as container, asking it to create an index named **public_health_index**. The **?pretty** option formats the response for easier reading.

* **-H 'Content-Type: application/json'**: Specifies that the data being sent is in JSON format.

* **-d '{...}'**: Provides the index configuration in JSON. The configurations include:

  * **"mappings":** Defines the schema for documents in this index.
    * **"properties":** Lists the fields for each document:
      * **"filename"**: Stores the document’s name as a keyword (for searching based on exact matches and for sorting).
      * **"data":** Stores the document’s content as binary (for base64-encoded files like PDFs before processing).

When you upload a document (with its data field containing base64-encoded content), the ingest pipeline processes this data using the **attachment processor**.

The attachment processor extracts the text content from the file and stores it in a new field, usually **file_content.content**.
This field (file_content.content) is automatically added to your documents after ingestion and is used for full-text search.

You should get a success response like:

```bash
{
  "acknowledged" : true,
  "shards_acknowledged" : true,
  "index" : "public_health_index"
}
```

### 5.3  Create an Ingest Pipeline for attachment

This command creates an ingest pipeline in Elasticsearch called **file_ingestor**.

1. It sends a PUT request to Elasticsearch to define a new pipeline named attachment.

2. The pipeline uses the **attachment processor**, which extracts text and metadata from any file type supported by Apache Tika, such as PDFs, Word documents, PowerPoint files, etc. as long as they are base64-encoded in the data field.
**Apache Tika** is a library that helps software to read the contents and metadata of files so that they can be searched or analyzed.
**Base64 encoding** turns binary data into text, making it safe to transmit in JSON and over HTTP. The ingest pipeline then decodes and processes this data.

3. The extracted content and metadata are saved into a new field called **file_content** in each document.
The description field is used to simply label the pipeline for clarity.

*In summary:* This pipeline enables Elasticsearch to automatically extract and index the text and metadata from uploaded files, making them searchable.

```bash
curl -XPUT 'localhost:9200/_ingest/pipeline/file_ingestor?pretty' -H 'Content-Type: application/json' -d'
{
  "description": "Extracts content from PDF files, Word documents, etc.",
  "processors": [
    {
      "attachment": {
        "field": "data",
        "target_field": "file_content"
      }
    }
  ]
}
'
```

You should get the following success response:

```bash
{
  "acknowledged" : true
}
```

### 5.4 Ingesting the Documents

We need to read each file in the ./index_ingest/health_records directory and send its content to Elasticsearch for indexing.
You can use a simple script (e.g., in Python or Bash) to automate this process. We will use a python script to ingesr all pdf files at once.

Example using a Manual steps: (Upload a Document (Base64-encoded))

---

This command "manually" uploads a document to Elasticsearch and processes it using the attachment pipeline:

1. It sends a PUT request to add a new document (with ID 1) to the index called "public_health_index".

2. The document includes a filename ("Dataset_Description_Asthma_Hospitalization_PORTAL_ONLY.pdf") and a data field that should contain the file’s contents, encoded as a base64 string. This means that you must convert the file to Base64 before sending it to Elasticsearch. You can do this using a script that reads the file and encodes it.

3. The **?pipeline=file_ingestor** part tells Elasticsearch to use the "file_ingestor" ingest pipeline, which extracts text and metadata from the file. The extracted content and its metadata are then stored in the document, making it searchable in Elasticsearch.

```bash
curl -X PUT "localhost:9200/public_health_index/_doc/1?pipeline=file_ingestor" -H "Content-Type: application/json" -d'
{
  "filename": "Dataset_Description_Asthma_Hospitalization_PORTAL_ONLY.pdf",
  "data": "BASE64_ENCODED_CONTENT_HERE"
}'
```

An alternative to the manual ingestion of one file at a time is to use a Python script to ingest multiple files.

This script goes through each PDF file, uploads it to Elasticsearch, converts its contents to Base64, uploads the converted Base64 to Elasticsearch as document, and sends a request to Elasticsearch to add a new document to the index. Each document includes the filename and the encoded file content.

```python
python scripts/file_ingestor_script.py data/public_health_reports
```

Expected output:

```bash
$ python scripts/file_ingestor_script.py data/public_health_reports
Indexing Kenya-Demographic-and-Health-Survey-2022-Factsheet-Baringo.pdf - Status Code: 201
Response: {"_index":"public_health_index","_id":"Kenya-Demographic-and-Health-Survey-2022-Factsheet-Baringo","_version":1,"result":"created","_shards":{"total":2,"successful":1,"failed":0},"_seq_no":0,"_primary_term":1}
Indexing Kenya-Demographic-and-Health-Survey-2022-Factsheet-Bomet.pdf - Status Code: 201
Response: {"_index":"public_health_index","_id":"Kenya-Demographic-and-Health-Survey-2022-Factsheet-Bomet","_version":1,"result":"created","_shards":{"total":2,"successful":1,"failed":0},"_seq_no":1,"_primary_term":1}
Indexing Kenya-Demographic-and-Health-Survey-2022-Factsheet-Bungoma.pdf - Status Code: 201
Response: {"_index":"public_health_index","_id":"Kenya-Demographic-and-Health-Survey-2022-Factsheet-Bungoma","_version":1,"result":"created","_shards":{"total":2,"successful":1,"failed":0},"_seq_no":2,"_primary_term":1}


//truncated

Indexing Kenya-Demographic-and-Health-Survey-2022-Main-Report-Volume-2.pdf - Status Code: 201
Response: {"_index":"public_health_index","_id":"Kenya-Demographic-and-Health-Survey-2022-Main-Report-Volume-2","_version":1,"result":"created","_shards":{"total":2,"successful":1,"failed":0},"_seq_no":49,"_primary_term":1}
Indexing Kenya-Demographic-and-Health-Survey-2022-Presentation.pdf - Status Code: 201
Response: {"_index":"public_health_index","_id":"Kenya-Demographic-and-Health-Survey-2022-Presentation","_version":1,"result":"created","_shards":{"total":2,"successful":1,"failed":0},"_seq_no":50,"_primary_term":1} 
Indexing Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf - Status Code: 201
Response: {"_index":"public_health_index","_id":"Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report","_version":1,"result":"created","_shards":{"total":2,"successful":1,"failed":0},"_seq_no":51,"_primary_term":1}
Finished processing PDF files.
```

### 6. Performing Queries

Now that the files have been converted into documents, which have been ingested, and then indexed, we can execute various types of queries via the Elasticsearch REST API.

First we can start with checking the mapping: You can verify the mapping of your index to see how the extracted content is being stored:

```bash
curl -XGET 'localhost:9200/public_health_index/_mapping?pretty'
```

This will show you the structure of your index and the fields that Elasticsearch has created.

Expected output:

```bash
$ curl -XGET 'localhost:9200/public_health_index/_mapping?pretty'
{
  "public_health_index" : {
    "mappings" : {
      "properties" : {
        "data" : {
          "type" : "binary"
        },
        "file_content" : {
          "properties" : {
            "author" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            },
            "content" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            },
            "content_length" : {
              "type" : "long"
            },
            "content_type" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            },
            "creator_tool" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            },
            "date" : {
              "type" : "date"
            },
            "format" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            },
            "language" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            },
            "modified" : {
              "type" : "date"
            },
            "title" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            }
          }
        },
        "filename" : {
          "type" : "keyword"
        }
      }
    }
  }
}
```

To search for the word "anthropometry", you should target the **file_content.content** field in your query.

```bash
curl -X POST "localhost:9200/public_health_index/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "file_content.content": "PowerPoint"
    }
  }
}'
```

If a query returns no results, it means that the word was either not present in the content of the PDFs you expected it to be in, or there might be some subtle differences in the text (e.g., case sensitivity, stemming) that are preventing a direct match.

Below is an alternative simpler search across all fields, not only the content:

```bash
curl -X POST "localhost:9200/public_health_index/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "query_string": {
      "query": "PowerPoint"
    }
  }
}
'
```

This is less efficient but can help you locate the term.

Sample output:

```bash
{
    "took": 932,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 1,
            "relation": "eq"
        },
        "max_score": 0.60996956,
        "hits": [
            {
                "_index": "public_health_index",
                "_id": "Kenya-Demographic-and-Health-Survey-2022-Presentation",
                "_score": 0.60996956,
                "_ignored": [
                    "file_content.content.keyword"
                ],
                "_source": {
                    "data": \\TRUNCATED
                    "file_content": {
                        "date": "2023-07-05T09:59:49Z",
                        "content_type": "application/pdf",
                        "author": "MK",
                        "format": "application/pdf; version=1.7",
                        "modified": "2023-08-25T11:45:22Z",
                        "language": "en",
                        "title": "Microsoft PowerPoint - 2022 KDHS Complete Presentation.pptx",
                        "content": \\TRUNCATED
                        "content_length": 92829
                    },
                    "filename": "Kenya-Demographic-and-Health-Survey-2022-Presentation.pdf"
                }
            }
        ]
    }
}
```

### 6.1. Basic Keyword Search

To search for documents containing a specific keyword (e.g., "fertility"):

```bash
curl -X POST "localhost:9200/public_health_index/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "file_content.content": "stillbirths"
    }
  }
}'
```

### 6.2. Phrase Search

To search for documents containing a specific phrase (e.g., "remote desktop connection"):

```bash
curl -XPOST 'localhost:9200/public_health_index/_search?pretty' -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_phrase": {
      "file_content.content": "Percent distribution of live births and stillbirths"
    }
  }
}
'
```

### 6.3. Boolean Queries

To combine multiple search conditions using must, should, and must_not (e.g., find documents containing "vaccination" but not "adult"):

```bash
curl -XPOST 'localhost:9200/public_health_index/_search?pretty' -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "match": { "file_content.content": "vaccination" } }
      ],
      "must_not": [
        { "match": { "file_content.content": "adult" } }
      ]
    }
  }
}
'
```

### 6.4. Wildcard Queries

To search for terms with wildcard characters (e.g., find files with titles conatining term "pre"):

```bash
$ curl -XPOST 'localhost:9200/public_health_index/_search?pretty' -H 'Content-Type: application/json' -d'
{
  "query": {
    "wildcard": {
      "file_content.title": "*pre*"
    }
  }
}
'
```

### 6.5. Fuzzy Queries

To find terms that are similar to the search term (allowing for typos): e.g cancr --> cancer

```bash
curl -XPOST 'localhost:9200/public_health_index/_search?pretty' -H 'Content-Type: application/json' -d'
{
  "query": {
    "fuzzy": {
      "file_content.content": {
        "value": "cancr",
        "fuzziness": 1
      }
    }
  }
}
'
```

### 7. Kibana provides a more user friendly way to perform searches as compared to the Elastic search API

By using Kibana's Discover interface and the methods described above, you can perform the same types of searches you were doing with curl in a more visual and interactive way.
Remember to select the correct index pattern and target the appropriate fields in your queries.

### 7.1 First create a data view for the public_health_index

What is a Data View?

A Data View tells Kibana which Elasticsearch indices you want to explore. It defines a set of one or more index names (or patterns) and configures how Kibana should interpret the fields in those indices, especially the timestamp field if you have time-based data.

Steps to Create a Data View:

a. Open Kibana in your web browser. The URL is http://localhost:5601 by default.

b. Navigate to *Stack Management*: In the left-hand navigation menu, look for *"Stack Management"*.

c. Go to *Data Views*: Within *Stack Management*, under the *"Kibana"* section, you will find *"Data Views"*. Click on *"Data Views"*.

Click *"Create data view"*: On the *Data Views page*, you will see a button labeled *"Create data view"*. Click on this button.

d. Define the Index Pattern:

In the *"Index pattern name"* field, enter the name or pattern that matches your Elasticsearch index(es).
For a specific index: If you want to create a Data View for your **public_health_index**, simply type public_health_index.

For multiple indices with a pattern: You can use wildcards (*) to match multiple indices. For example, logstash-* would match all indices starting with "logstash-". If you wanted to include all indices, you could use *.

As you type, Kibana will show you a list of matching indices in Elasticsearch. Verify that your intended index (public_health_index) is listed.

*Configure the Timestamp Field (Optional but Recommended for Time Series Data):*
If your index contains a field that represents a timestamp, Kibana will ask you to configure it as the "Timestamp field". This is crucial for time-based visualizations and analysis.

In this scenario of indexing PDF reports, you might not have an explicit timestamp field within the extracted content or the metadata you have explicitly mapped. However, Elasticsearch automatically adds @timestamp when a document is indexed.

If you have a specific date field within your file_content (like file_content.date or file_content.modified), you can select that field if you want to analyze your reports based on their extracted dates.
If your data is not inherently time-based, you can choose *"I don't want to use a Time Filter".*

In this scenario, we select **file_content.modified**

e. Click "Save data view to Kibana" once you have entered the index pattern and (optionally) configured the timestamp field.

Data View Created: You will be redirected back to the Data Views list, and your newly created Data View (public_health_index) should now be listed.

f. Using Your Data View:

Once your Data View is created, you can use it in various Kibana applications:

*Discover:* When you go to "Discover", you can select your public_health_index Data View from the dropdown menu to explore and search your indexed PDF data.

*Visualize:* When creating visualizations, you can choose your public_health_index Data View as the data source.

*Dashboard:* You can build dashboards using visualizations based on your public_health_index Data View.

*Canvas:* For creating quality presentations.

By following these steps, you can successfully create a Data View in Kibana that points to your **public_health_index**, allowing you to visually explore and analyze the content of your indexed PDF files.

### 7. 2 We can then perform Information retrieval from Kibana

Accessing Kibana's Discover Interface

The primary tool for searching and exploring your data in Kibana is the Discover interface. You can usually find it in the main navigation menu on the left-hand side.

### 7.2.1 Basic Keyword Search ("malaria")

Open Discover: Click on the *"Discover"* icon in the Kibana navigation.

Select Index Pattern: You will be prompted to select an index pattern. Choose public_health_index. If it's not listed, you might need to create it in Kibana's Index Management (gear icon in the navigation). When creating the index pattern, simply type public_health_index* to match your index.

Search Bar: You should see a search bar at the top. To perform a basic keyword search, simply type your keyword directly into the search bar and press Enter or click the magnifying glass icon.

* malaria*

Kibana will search across all indexed fields for this term.

### 7.2.2 Targeting a Specific Field: To specifically search within the file_content.content field, use the following syntax in the search bar:### 

Paste on search tab: `file_content.content: "death"`

Press Enter or click the magnifying glass.

### 7.2.3 Phrase Search ("premature death among individuals")

Paste on search tab: `file_content.content: "Percent distribution of live births and stillbirths"`

Press Enter or click the magnifying glass. Kibana will look for this exact sequence of words.

### 7.2.4 Boolean Queries (containing "teens" but not "preterm")

Search Bar: You can construct boolean queries using the AND, OR, and NOT operators (they must be in uppercase).

To find documents containing "teens" and NOT containing "preterm" in file_content.content:

Paste on search tab:  `file_content.content: "vaccination" AND NOT file_content.content: "adult"`

Press Enter or click the magnifying glass.

Paste on search tab:  file_content.content: teens or file_content.content: preterm

### 7.2.4 Wildcard Queries (titles containing "pre")

Open Discover and Select Index Pattern.

Search Bar: To perform a wildcard search on the file_content.title field for titles containing "pre", use the * wildcard character:

`file_content.title : *pre*`

Click "Run".