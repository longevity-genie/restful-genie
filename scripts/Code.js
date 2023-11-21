function onOpen(){

}

/**
 * Retrieves cached data for a given key.
 *
 * @param {string} cacheKey - The key to retrieve data for.
 * @return {Object|null} Cached data or null if not found.
 */
function getCachedData(cacheKey) {
  var cache = CacheService.getScriptCache();
  var cachedResponse = cache.get(cacheKey);
  if (cachedResponse != null) {
    return JSON.parse(cachedResponse);
  }
  return null; // No cached data found
}


/**
 * Generates a cache key based on provided arguments.
 *
 * @param {Array} args - Array of arguments to generate the key from.
 * @return {string} The generated cache key.
 */
function generateCacheKey(args) {
  var keyString = args.join('-');
  var keyBytes = Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, keyString, Utilities.Charset.UTF_8);
  var cacheKey = keyBytes.map(function(byte) {
    var byteHex = (byte < 0 ? byte + 256 : byte).toString(16);
    return byteHex.length === 1 ? '0' + byteHex : byteHex;
  }).join('');
  return cacheKey;
}


/**
 * Updates the cache with new data.
 *
 * @param {string} cacheKey - The key to update data for.
 * @param {Object} data - The data to cache.
 * @param {number} cacheTime - Time in seconds to keep the data in cache.
 */
function updateCache(cacheKey, data, cacheTime) {
  var cache = CacheService.getScriptCache();
  cache.put(cacheKey, JSON.stringify(data), cacheTime);
}

/**
 * Main function to download a paper.
 *
 * @param {string} doi - The DOI of the paper.
 * @param {boolean} [selenium_on_fail=true] - Use Selenium on failure.
 * @param {boolean} [scihub_on_fail=true] - Use SciHub on failure.
 * @param {number} [cache_seconds=3600] - Cache duration in seconds, no cache if <=0
 * @param {string} [parser="py_mu_pdf"] - Parser to use.
 * @param {boolean} [subfolder=true] - Whether to use subfolders.
 * @param {boolean} [do_not_reparse=true] - Flag to avoid reparsing.
 * @param {number} [selenium_min_wait=15] - Minimum wait time for Selenium.
 * @param {number} [selenium_max_wait=60] - Maximum wait time for Selenium.
 * @return {Object} Downloaded paper data or error info.
 */
function DOWNLOAD_PAPER(doi, selenium_on_fail, scihub_on_fail, cache_seconds, parser, subfolder, do_not_reparse, selenium_min_wait, selenium_max_wait) {
  // Handling default values
  selenium_on_fail = (selenium_on_fail === undefined) ? true : selenium_on_fail;
  scihub_on_fail = (scihub_on_fail === undefined) ? true : scihub_on_fail;
  parser = (parser === undefined) ? "py_mu_pdf" : parser;
  subfolder = (subfolder === undefined) ? true : subfolder;
  do_not_reparse = (do_not_reparse === undefined) ? true : do_not_reparse;
  selenium_min_wait = (selenium_min_wait === undefined) ? 15 : selenium_min_wait;
  selenium_max_wait = (selenium_max_wait === undefined) ? 60 : selenium_max_wait;
  cache_seconds = (cache_seconds === undefined) ? 3600 : cache_seconds;

  // Generate the cache key
  var cacheKey = generateCacheKey([doi, selenium_on_fail, scihub_on_fail, parser, subfolder, do_not_reparse, selenium_min_wait, selenium_max_wait]);

  // Check if the response is already in the cache
  var cachedData = getCachedData(cacheKey);
  if (cachedData != null) {
    return cachedData;
  }

  // Define the FastAPI endpoint URL and payload for the POST request
  var fastApiUrl = 'http://agingkills.eu:8000/download_paper/';
  var payload = {
    "doi": doi,
    "selenium_on_fail": selenium_on_fail,
    "scihub_on_fail": scihub_on_fail,
    "parser": parser,
    "subfolder": subfolder,
    "do_not_reparse": do_not_reparse,
    "selenium_min_wait": selenium_min_wait,
    "selenium_max_wait": selenium_max_wait
  };

  // Options for the POST request
  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'payload': JSON.stringify(payload)
  };
  console.info(options);

  // Make the request and handle errors
  try {
    var response = UrlFetchApp.fetch(fastApiUrl, options);
    var responseText = response.getContentText();

    // Parse the response and cache it if successful
    var result = JSON.parse(responseText);
    console.info(result);
    if (cache_seconds > 0 && response.getResponseCode() == 200) {
      updateCache(cacheKey, result, cache_seconds);
    }

    return result.pdf; // Assuming the response contains a 'pdf' field
  } catch (e) {
    Logger.log("Error in download_paper: " + e.toString());
    return { "error": true, "message": e.toString() };
  }
}

function GPT(textValue, model_name='gpt-3.5-turbo', temperature=0.0, resplit = true, parse_escaped_quotes = true, host='http://agingkills.eu:8000', api = "/gpt", limit=1, cache_seconds = 3600) {
  // Generate the cache key
  var cacheKey = generateCacheKey([textValue, model_name]);

  // Check if the response is already in the cache
  var cachedData = getCachedData(cacheKey);
  if (cachedData != null) {
    return cachedData;
  }

  // Prepare the data for the API call
  var data = {
    'model_name': model_name,
    'temperature': temperature,
    'text': textValue
  };

  var options = {
    'method' : 'post',
    'contentType': 'application/json',
    'payload' : JSON.stringify(data)
  };

  // Make the API call using the provided host and API endpoint
  var response = UrlFetchApp.fetch(host + api, options);
  var responseText = response.getContentText();

  // Replace \n with new lines if resplit is true
  if (resplit) {
    responseText = responseText.replace(/\\n/g, "\n");
  }

  // Replace escaped quotes with normal quotes if parse_escaped_quotes is true
  if (parse_escaped_quotes) {
    responseText = responseText.replace(/\\"/g, '"');
  }

  // Cache the new response if caching is enabled
  if (cache_seconds > 0) {
    updateCache(cacheKey, responseText, cache_seconds);
  }

  return responseText;
}



function GPT_3_5(textValue, temperature=0.0, cache_seconds = 3600) {
    return GPT(textValue, model_name='gpt-3.5-turbo', temperature=temperature, cache_seconds=cache_seconds)
}

function GPT4(textValue, temperature=0.0, cache_seconds = 3600) {
    //just an alias to GPT_4
    return GPT(textValue, model_name='gpt-4', temperature=temperature, cache_seconds=cache_seconds)
}

function GPT_4(textValue, temperature=0.0, cache_seconds = 3600) {
    return GPT(textValue, model_name='gpt-4', temperature=temperature, cache_seconds=cache_seconds)
}

function SEMANTIC_SEARCH(textValue, limit=1, collection_name='bge_base_en_v1.5_aging_5', host='http://agingkills.eu:8000', api = "/semantic_search", with_vectors=false, with_payload=true, resplit = true, cache_seconds = 3600) {
  // Generate the cache key using the generateCacheKey function
  var cacheKey = generateCacheKey([textValue, collection_name, limit]);

  // Check if caching is enabled and if the response is already in the cache
  var cachedData = getCachedData(cacheKey);
  if (cachedData != null) {
    return cachedData;
  }

  // If not cached or cache is disabled, proceed with the API call
  var data = {
    'text': textValue,
    'collection_name': collection_name,
    'with_vectors': with_vectors,
    'with_payload': with_payload,
    'limit': limit
  };

  var options = {
    'method' : 'post',
    'contentType': 'application/json',
    'payload' : JSON.stringify(data)
  };

  // Make the request and handle errors
  try {
    var url = host + api;
    var response = UrlFetchApp.fetch(url, options);
    var responseText = response.getContentText();;

    // Parse the response and cache it if successful
    var result = JSON.parse(responseText);
    console.info(result);
    if (cache_seconds > 0 && response.getResponseCode() == 200) {
      updateCache(cacheKey, result, cache_seconds);
    }
    if (result != null && result.length ==1) return result[0]
    return result; // Assuming the response contains a 'pdf' field
  } catch (e) {
    Logger.log("Error in download_paper: " + e.toString());
    return { "error": true, "message": e.toString() };
  }
}



function FLATTEN_JSON(jsonString) {
  // Check if the string starts with "{ and ends with }", and remove these characters if it does
  if (jsonString.startsWith('"{') && jsonString.endsWith('}"')) {
    jsonString = jsonString.substring(1, jsonString.length - 1);
  }

  // Initialize an array to hold the values
  var values = [];

  // Parse the JSON string into an object
  try {
    var jsonObject = JSON.parse(jsonString);
  } catch (e) {
    return [['Error parsing JSON: ' + e.message]];
  }

  // Function to recursively flatten the JSON object
  function flattenObject(obj) {
    Object.keys(obj).forEach(key => {
      if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
        // For nested objects, call the function recursively
        flattenObject(obj[key]);
      } else {
        // For primitive values or arrays, add the value to the values array
        values.push(JSON.stringify(obj[key]));
      }
    });
  }

  // Start the flattening process
  flattenObject(jsonObject);

  // Return the values as a single row
  return [values];
}