import os, arcpy, datetime

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                FUNCTION:    Delete AGOL Features

def AGOL_Delete_Features(name_of_FS, index_of_layer_in_FS, object_ids, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      index_of_layer_in_FS (int): The index of the layer in the Feature Service.
        This will frequently be 0, but it could be a higer number if the FS has
        multiple layers in it.
      object_ids (list of str): List of OBJECTID's that should be deleted.
      token (str): Obtained from the Get_Token().

    RETURNS:
      None

    FUNCTION:
      To Delete features on an AGOL Feature Service.
    """

    print '--------------------------------------------------------------------'
    print "Starting Delete_AGOL_Features()"
    import urllib2, urllib, json

    # Turn the list of object_ids into one string with comma separated IDs
    object_ids_str = ','.join(str(x) for x in object_ids)

    # Set URLs
    delete_url       = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/{}/deleteFeatures?token={}'.format(name_of_FS, index_of_layer_in_FS, token)
    del_params       = urllib.urlencode({'objectIds': object_ids_str, 'f':'json'})


    # Delete the features
    print '  Deleting Features in FS: "{}" and index "{}"'.format(name_of_FS, index_of_layer_in_FS)
    print '  OBJECTIDs to be deleted: {}'.format(object_ids_str)
    ##print delete_url + del_params
    response  = urllib2.urlopen(delete_url, del_params)
    response_json_obj = json.load(response)
    ##print response_json_obj

    for result in response_json_obj['deleteResults']:
        ##print result
        print '    OBJECTID: {}'.format(result['objectId'])
        print '      Deleted? {}'.format(result['success'])

    print 'Finished Delete_AGOL_Features()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         FUNCTION:   Get Attachments
# Attachments (images) are obtained by hitting the REST endpoint of the feature
# service (gaURL) and returning a URL that downloads a JSON file (which is a
# replica of the database).  The script then uses that downloaded JSON file to
# get the URL of the actual images.  The JSON file is then used to get the
# StationID and SampleEventID of the related feature so they can be used to name
# the downloaded attachment.

#TODO: find a way to rotate the images clockwise 90-degrees

# This function is DEPRICATED.  Better to use stand alone script
# Download_AGOL_Attachments_All.py
def AGOL_Get_Attachments(token, gaURL, gaFolder, SmpEvntIDs_dl, dt_to_append):
    """
    PARAMETERS:
        token (str):
            The string token obtained in FUNCTION Get_Token().
        gaURL (str):
            The variable set in FUNCTION main() where we can request to create a
            replica FGDB in json format.
        wkgFolder (str):
            The variable set in FUNCTION main() which is a path to our working
            folder.
        dt_to_append (str):
            The date and time string returned by FUNCTION Get_DateAndTime().

    VARS:
        replicaUrl (str):
            URL of the replica FGDB in json format.
        JsonFileName (str):
            Name of the temporary json file.
        gaFolder (str):
            A folder in the wkgFolder that holds the attachments.
        gaRelId (str):
            The parentGlobalId of the attachment.  This = the origId for the
            related feature.
        origId (str):
            The GlobalId of the feature.  This = the parentGlobalId of the
            related attachment.
        origName1 (str):
            The StationID of the related feature to the attachment.
        origName2 (str):
            The SampleEventID of the related feature to the attachment.
        attachName (str):
            The string concatenation of origName1 and origName2 to be used to
            name the attachment.
        dupList (list of str):
            List of letters ('A', 'B', etc.) used to append to the end of an
            image to prevent multiple images with the same StationID and
            SampleEventID overwriting each other.
        attachmentUrl:
            The URL of each specific attachment.  Need a token to actually
            access and download the image at this URL.

    RETURNS:
        gaFolder (str):
            So that the email can send that information.

    FUNCTION:
      Gets the attachments (images) that are related to the database features and
      stores them as .jpg in a local file inside the wkgFolder.
    """

    print '--------------------------------------------------------------------'
    print 'Getting Attachments...'

    # Flag to set if Attachments were downloaded.  Set to 'True' if downloaded
    attachment_dl = False

    #---------------------------------------------------------------------------
    #                       Get the attachments url (ga)
    # Set the values in a dictionary
    gaValues = {
    'f' : 'json',
    'replicaName' : 'Bacteria_TMDL_Replica',
    'layers' : '0',
    'geometryType' : 'esriGeometryPoint',
    'transportType' : 'esriTransportTypeUrl',
    'returnAttachments' : 'true',
    'returnAttachmentDatabyURL' : 'false',
    'token' : token
    }

    # Get the Replica URL
    print '  Getting Replica URL'
    gaData = urllib.urlencode(gaValues)
    gaRequest = urllib2.Request(gaURL, gaData)
    gaResponse = urllib2.urlopen(gaRequest)
    gaJson = json.load(gaResponse)
    try:
        replicaUrl = gaJson['URL'] # Try to load the 'URL' key of the replica

    # If the 'URL' key doesn't exist, print out the error message and details
    except KeyError:
        print '*** Key Error! ***'
        print '  {}\n  {}'.format(gaJson['error']['message'], gaJson['error']['details'])
        print '  Replica URL: %s' % str(replicaUrl)  # For testing purposes

    # Set the token into the URL so it can be accessed
    replicaUrl_token = replicaUrl + '?&token=' + token + '&f=json'
    ##print '  Replica URL Token: %s' % str(replicaUrl_token)  # For testing purposes

    #---------------------------------------------------------------------------
    #                         Save the JSON file
    # Access the URL and save the file to the current working directory named
    # 'myLayer.json'.  This will be a temporary file and will be deleted

    JsonFileName = 'Temp_JSON_%s.json' % dt_to_append

    # Save the file
    # NOTE: the file is saved to the 'current working directory' + 'JsonFileName'
    urllib.urlretrieve(replicaUrl_token, JsonFileName)

    # Allow the script to access the saved JSON file
    cwd = os.getcwd()  # Get the current working directory
    jsonFilePath = cwd + '\\' + JsonFileName # Path to the downloaded json file
    print '  Temp JSON file saved to: ' + jsonFilePath

    #---------------------------------------------------------------------------
    #                       Save the attachments

    # Make the gaFolder (to hold attachments) if it doesn't exist.
    if not os.path.exists(gaFolder):
        os.makedirs(gaFolder)

    # Open the JSON file
    with open (jsonFilePath) as data_file:
        data = json.load(data_file)

    # Save the attachments
    # Loop through each 'attachment' and get its parentGlobalId so we can name
    #  it based on its corresponding feature
    print '  Attempting to save attachments:'

    for attachment in data['layers'][0]['attachments']:
        gaRelId = attachment['parentGlobalId']

        # Now loop through all of the 'features' and break once the corresponding
        #  GlobalId's match so we can save based on the 'StationID'
        #  and 'SampleEventID'
        for feature in data['layers'][0]['features']:
            origId = feature['attributes']['globalid']
            StationID = feature['attributes']['StationID']
            SampleEventID = str(feature['attributes']['SampleEventID'])
            if origId == gaRelId:
                break

        # Test to see if the StationID is one of the features downloaded in
        # FUNCTION Get_Data. Download if so, ignore if not
        if SampleEventID in SmpEvntIDs_dl:
            attachName = '%s__%s' % (StationID, SampleEventID)
            # 'i' and 'dupList' are used in the event that there are
            #  multiple photos with the same StationID and SampleEventID.  If they
            #  do have the same attributes as an already saved attachment, the letter
            #  suffix at the end of the attachment name will increment to the next
            #  letter.  Ex: if there are two SDR-100__9876, the first will always be
            #  named 'SDR-1007__9876_A.jpg', the second will be 'SDR-1007__9876_B'
            i = 0
            dupList = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            attachPath = gaFolder + '\\' + attachName + '_' + dupList[i] + '.jpg'

            # Test to see if the attachPath currently exists
            while os.path.exists(attachPath):
                # The path does exist, so go through the dupList until a 'new' path is found
                i += 1
                attachPath = gaFolder + '\\' + attachName + '_' + dupList[i] + '.jpg'

                # Test the new path to see if it exists.  If it doesn't exist, break out
                # of the while loop to save the image to that new path
                if not os.path.exists(attachPath):
                    break

            # Only download the attachment if the picture is from A - G
            # 'H' is a catch if there are more than 7 photos with the same Station ID
            # and Sample Event ID, shouldn't be more than 7 so an 'H' pic is passed.
            if (dupList[i] != 'H'):
                # Get the token to download the attachment
                gaValues = {'token' : token }
                gaData = urllib.urlencode(gaValues)

                # Get the attachment and save as attachPath
                print '    Saving %s' % attachName
                attachment_dl = True

                attachmentUrl = attachment['url']
                urllib.urlretrieve(url=attachmentUrl, filename=attachPath,data=gaData)

            else:
                print '  WARNING.  There were more than 7 pictures with the same Station ID and Sample Event ID. Picture not saved.'

    if (attachment_dl == False):
        print '    No attachments saved this run.  OK if no attachments submitted since last run.'

    print '  All attachments can be found at: %s' % gaFolder

    # Delete the JSON file since it is no longer needed.
    print '  Deleting JSON file'
    os.remove(jsonFilePath)

    print 'Successfully got attachments.\n'

    return gaFolder

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                             FUNCTION Get_AGOL_Data_All()
def AGOL_Get_Data_All(AGOL_fields, token, FS_url, index_of_layer, wkg_folder, wkg_FGDB, FC_name):
    """
    PARAMETERS:
      AGOL_fields (str) = The fields we want to have the server return from our query.
        use the string ('*') to return all fields.
      token (str) = The token obtained by the Get_Token() which gives access to
        AGOL databases that we have permission to access.
      FS_url (str) = The URL address for the feature service.
        Should be the service URL on AGOL (up to the '/FeatureServer' part).
      index_of_layer (int)= The index of the specific layer in the FS to download.
        i.e. 0 if it is the first layer in the FS, 1 if it is the second layer, etc.
      wkg_folder (str) = Full path to the folder that contains the FGDB that you
        want to download the data into.  Folder must already exist.
      wkg_FGDB (str) = Name of the working FGDB in the wkg_folder.  FGDB must
        already exist.
      FC_name (str) = The name of the FC that will be created to hold the data
        downloaded by this function.  This FC gets overwritten every time the
        script is run.  FC does NOT need to already exist.

    RETURNS:
      None

    FUNCTION:
      To download ALL data from a layer in a FS on AGOL, using OBJECTIDs.
      This function, establishs a connection to the
      data, finds out the number of features, gets the highest and lowest OBJECTIDs,
      and the maxRecordCount returned by the server, and then loops through the
      AGOL data and downloads it to the FGDB.  The first time the data is d/l by
      the script it will create a FC.  Any subsequent loops will download the
      next set of data and then append the data to the first FC.  This looping
      will happen until all the data has been downloaded and appended to the one
      FC created in the first loop.

    NOTE:
      Need to have obtained a token from the Get_Token() function.
      Need to have an existing FGDB to download data into.
    """
    print '--------------------------------------------------------------------'
    print 'Starting Get_AGOL_Data_All()'

    import urllib2, json, urllib

    # Set URLs
    query_url = FS_url + '/{}/query'.format(index_of_layer)
    print '  Downloading all data found at: {}/{}\n'.format(FS_url, index_of_layer)

    #---------------------------------------------------------------------------
    #        Get the number of records are in the Feature Service layer

    # This query returns ALL the OBJECTIDs that are in a FS regardless of the
    #   'max records returned' setting
    query = "?where=1=1&returnIdsOnly=true&f=json&token={}".format(token)
    obj_count_URL = query_url + query
    ##print obj_count_URL  # For testing purposes
    response = urllib2.urlopen(obj_count_URL)  # Send the query to the web
    obj_count_json = json.load(response)  # Store the response as a json object
    try:
        object_ids = obj_count_json['objectIds']
    except:
        print 'ERROR!'
        print obj_count_json['error']['message']

    num_object_ids = len(object_ids)
    print '  Number of records in FS layer: {}'.format(num_object_ids)

    #---------------------------------------------------------------------------
    #                  Get the lowest and highest OBJECTID
    object_ids.sort()
    lowest_obj_id = object_ids[0]
    highest_obj_id = object_ids[num_object_ids-1]
    print '  The lowest OBJECTID is: {}\n  The highest OBJECTID is: {}'.format(\
                                                  lowest_obj_id, highest_obj_id)

    #---------------------------------------------------------------------------
    #               Get the 'maxRecordCount' of the Feature Service
    # 'maxRecordCount' is the number of records the server will return
    # when we make a query on the data.
    query = '?f=json&token={}'.format(token)
    max_count_url = FS_url + query
    ##print max_count_url  # For testing purposes
    response = urllib2.urlopen(max_count_url)
    max_record_count_json = json.load(response)
    max_record_count = max_record_count_json['maxRecordCount']
    print '  The max record count is: {}\n'.format(str(max_record_count))


    #---------------------------------------------------------------------------

    # Set the variables needed in the loop below
    start_OBJECTID = lowest_obj_id  # i.e. 1
    end_OBJECTID   = lowest_obj_id + max_record_count - 1  # i.e. 1000
    last_dl_OBJECTID = 0  # The last downloaded OBJECTID
    first_iteration = True  # Changes to False at the end of the first loop

    while last_dl_OBJECTID <= highest_obj_id:
        where_clause = 'OBJECTID >= {} AND OBJECTID <= {}'.format(start_OBJECTID, end_OBJECTID)

        # Encode the where_clause so it is readable by URL protocol (ie %27 = ' in URL).
        # visit http://meyerweb.com/eric/tools/dencoder to test URL encoding.
        # If you suspect the where clause is causing the problems, uncomment the
        #   below 'where = "1=1"' clause.
        ##where_clause = "1=1"  # For testing purposes
        print '  Getting data where: {}'.format(where_clause)
        where_encoded = urllib.quote(where_clause)
        query = "?where={}&outFields={}&returnGeometry=true&f=json&token={}".format(where_encoded, AGOL_fields, token)
        fsURL = query_url + query

        # Create empty Feature Set object
        fs = arcpy.FeatureSet()

        #---------------------------------------------------------------------------
        #                 Try to load data into Feature Set object
        # This try/except is because the fs.load(fsURL) will fail whenever no data
        # is returned by the query.
        try:
            ##print 'fsURL %s' % fsURL  # For testing purposes
            fs.load(fsURL)
        except:
            print '*** ERROR, data not downloaded ***'

        #-----------------------------------------------------------------------
        # Process d/l data

        if first_iteration == True:  # Then this is the first run and d/l data to the FC_name
            path = wkg_folder + "\\" + wkg_FGDB + '\\' + FC_name
        else:
            path = wkg_folder + "\\" + wkg_FGDB + '\\temp_to_append'

        #Copy the features to the FGDB.
        print '    Copying AGOL database features to: %s' % path
        arcpy.CopyFeatures_management(fs,path)

        # If this is a subsequent run then append the newly d/l data to the FC_name
        if first_iteration == False:
            orig_path = wkg_folder + "\\" + wkg_FGDB + '\\' + FC_name
            print '    Appending:\n      {}\n      To:\n      {}'.format(path, orig_path)
            arcpy.Append_management(path, orig_path, 'NO_TEST')

            print '    Deleting temp_to_append'
            arcpy.Delete_management(path)

        # Set the last downloaded OBJECTID
        last_dl_OBJECTID = end_OBJECTID

        # Set the starting and ending OBJECTID for the next iteration
        start_OBJECTID = end_OBJECTID + 1
        end_OBJECTID   = start_OBJECTID + max_record_count - 1

        # If we reached this point we have gone through one full iteration
        first_iteration = False
        print ''

    if first_iteration == False:
        print "  Successfully retrieved data.\n"
    else:
        print '  * WARNING, no data was downloaded. *'

    print 'Finished Get_AGOL_Data_All()'

    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                             FUNCTION Get_AGOL_Data_Where()
def AGOL_Get_Data_Where(AGOL_fields, token, FS_url, index_of_layer, where_clause, wkg_folder, wkg_FGDB, orig_FC):
    """
    PARAMETERS:
      AGOL_fields (str) = The fields we want to have the server return from our query.
        use the string ('*') to return all fields.
      token (str) = The token obtained by the Get_Token() which gives access to
        AGOL databases that we have permission to access.
      FS_url (str) = The URL address for the feature service.
        Should be the service URL on AGOL (up to the '/FeatureServer' part).
      index_of_layer (int)= The index of the specific layer in the FS to download.
        i.e. 0 if it is the first layer in the FS, 1 if it is the second layer, etc.
      where_clause (str) = The where clause to add to the query to receive a
        subset of the full dataset.
      wkg_folder (str) = Full path to the 'Data' folder that contains the FGDB's,
        Excel files, Logs, and Pictures.
      wkg_FGDB (str) = Name of the working FGDB in the wkgFolder.
      orig_FC (str) = Name of the FC that will hold the original data downloaded
        by this function.  This FC gets overwritten every time the script is run.

    RETURNS:
      None

    FUNCTION:
      Uses a where_clause to download a subset of data from the FS.
      To download data from AGOL.  This function, establishs a connection to the
      data, creates a FGDB (if needed), creates a FC (or overwrites the existing
      one to store the data, and then copies the data from AGOL to the FC.

    NOTE:
      Need to have obtained a token from the Get_Token() function.
    """

    print 'Starting Get_AGOL_Data()'

    # Set URLs
    query_url = FS_url + '/{}/query'.format(index_of_layer)

    # Encode the where_clause so it is readable by URL protocol (ie %27 = ' in URL).
    # visit http://meyerweb.com/eric/tools/dencoder to test URL encoding.
    # If you suspect the where clause is causing the problems, uncomment the
    #   below 'where = "1=1"' clause.
    ##where_clause = "1=1"  # For testing purposes
    print '  Getting data where: {}'.format(where_clause)
    where_encoded = urllib.quote(where_clause)
    query = "?where={}&outFields={}&returnGeometry=true&f=json&token={}".format(where_encoded, AGOL_fields, token)
    fsURL = query_url + query

    # Create empty Feature Set object
    fs = arcpy.FeatureSet()

    #---------------------------------------------------------------------------
    #                 Try to load data into Feature Set object
    # This try/except is because the fs.load(fsURL) will fail whenever no data
    # is returned by the query.
    try:
        ##print 'fsURL %s' % fsURL  # For testing purposes
        fs.load(fsURL)
    except:
        print '  "fs.load(fsURL)" yielded no data at fsURL.'
        print '  Query may not have yielded any records.'
        print '  Could simply mean there was no data satisfied by the query.'
        print '  Or could be another problem with the Get_AGOL_Data() function.'
        print '  Feature Service: %s' % str(fsURL)

        # If no data downloaded, stop the function here
        print '\n  * WARNING, no data downloaded *'
        print 'Finished Get_AGOL_Data()'
        return

    #---------------------------------------------------------------------------
    #             Data was loaded, CONTINUE the downloading process

    #Create working FGDB if it does not already exist. Leave alone if it does...
    FGDB_path = wkg_folder + '\\' + wkg_FGDB
    if not os.path.exists(FGDB_path):
        print '  Creating FGDB: %s at: %s' % (wkg_FGDB, wkg_folder)

        # Process
        arcpy.CreateFileGDB_management(wkg_folder,wkg_FGDB)

    #---------------------------------------------------------------------------
    #Copy the features to the FGDB.
    orig_path = wkg_folder + "\\" + wkg_FGDB + '\\' + orig_FC
    print '  Copying AGOL database features to: %s' % orig_path

    # Process
    arcpy.CopyFeatures_management(fs,orig_path)

    #---------------------------------------------------------------------------
    print "  Successfully retrieved data.\n"
    print 'Finished Get_AGOL_Data()'

    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                FUNCTION:    Get AGOL Object IDs Where

def AGOL_Get_Object_Ids_Where(name_of_FS, index_of_layer_in_FS, where_clause, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      index_of_layer_in_FS (int): The index of the layer in the Feature Service.
        This will frequently be 0, but it could be a higer number if the FS has
        multiple layers in it.
      where_clause (str): Where clause. i.e.:
        where_clause = "FIELD_NAME = 'Value in field'"
      token (str): Obtained from the Get_Token()

    RETURNS:
      object_ids (list of str): List of OBJECTID's that satisfied the
      where_clause.

    FUNCTION:
      To get a list of the OBJECTID's of the features that satisfied the
      where clause.  This list will be the full list of all the records in the
      FS regardless of the number of the returned OBJECTID's or the max record
      count for the FS.

    NOTE: This function assumes that you have already gotten a token from the
    Get_Token() and are passing it to this function via the 'token' variable.
    """

    print '--------------------------------------------------------------------'
    print "Starting Get_AGOL_Object_Ids_Where()"
    import urllib2, urllib, json

    # Create empty list to hold the OBJECTID's that satisfy the where clause
    object_ids = []

    # Encode the where_clause so it is readable by URL protocol (ie %27 = ' in URL).
    # visit http://meyerweb.com/eric/tools/dencoder to test URL encoding.
    where_encoded = urllib.quote(where_clause)

    # Set URLs
    query_url = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/{}/query'.format(name_of_FS, index_of_layer_in_FS)
    query = '?where={}&returnIdsOnly=true&f=json&token={}'.format(where_encoded, token)
    get_object_id_url = query_url + query

    # Get the list of OBJECTID's that satisfied the where_clause

    print '  Getting list of OBJECTID\'s that satisfied the where clause for layer:\n    {}'.format(query_url)
    print '  Where clause: "{}"'.format(where_clause)
    response = urllib2.urlopen(get_object_id_url)
    response_json_obj = json.load(response)
    try:
        object_ids = response_json_obj['objectIds']
    except KeyError:
        print '***ERROR!  KeyError! ***'
        print '  {}\n'.format(response_json_obj['error']['message'])
        print '  If you receive "Invalid URL", are you sure you have the correct FS name?'

    if len(object_ids) > 0:
        print '  There are "{}" features that satisfied the query.'.format(len(object_ids))
        print '  OBJECTID\'s of those features:'
        for obj in object_ids:
            print '    {}'.format(obj)

    else:
        print '  No features satisfied the query.'

    print "Finished Get_AGOL_Object_Ids_Where()\n"

    return object_ids

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION:    Get AGOL token
def AGOL_Get_Token(cfgFile, gtURL="https://www.arcgis.com/sharing/rest/generateToken"):
    """
    PARAMETERS:
      cfgFile (str):
        Path to the .txt file that holds the user name and password of the
        account used to access the data.  This account must be in a group
        that has access to the online database.
        The format of the config file should be as below with
        <username> and <password> completed:

          [AGOL]
          usr: <username>
          pwd: <password>

      gtURL {str}: URL where ArcGIS generates tokens. OPTIONAL.

    VARS:
      token (str):
        a string 'password' from ArcGIS that will allow us to to access the
        online database.

    RETURNS:
      token (str): A long string that acts as an access code to AGOL servers.
        Used in later functions to gain access to our data.

    FUNCTION: Gets a token from AGOL that allows access to the AGOL data.
    """

    print '--------------------------------------------------------------------'
    print "Getting Token..."

    import ConfigParser, urllib, urllib2, json

    # Get the user name and password from the cfgFile
    configRMA = ConfigParser.ConfigParser()
    configRMA.read(cfgFile)
    usr = configRMA.get("AGOL","usr")
    pwd = configRMA.get("AGOL","pwd")

    # Create a dictionary of the user name, password, and 2 other keys
    gtValues = {'username' : usr, 'password' : pwd, 'referer' : 'http://www.arcgis.com', 'f' : 'json' }

    # Encode the dictionary so they are in URL format
    gtData = urllib.urlencode(gtValues)

    # Create a request object with the URL adn the URL formatted dictionary
    gtRequest = urllib2.Request(gtURL,gtData)

    # Store the response to the request
    gtResponse = urllib2.urlopen(gtRequest)

    # Store the response as a json object
    gtJson = json.load(gtResponse)

    # Store the token from the json object
    token = gtJson['token']
    ##print token  # For testing purposes

    print "Successfully retrieved token.\n"

    return token

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                 FUNCTION:  Query AGOL Features
def AGOL_Query_Features(name_of_FS, index_of_layer_in_FS, object_ids, fields_to_report, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      index_of_layer_in_FS (int): The index of the layer in the Feature Service.
        This will frequently be 0, but it could be a higer number if the FS has
        multiple layers in it.
      object_ids (list of str): List of OBJECTID's that should be querried.
      fields_to_report (list of str): List of fields in the database that should
        be reported on.
      token (str): Obtained from the Get_Token().

    RETURNS:
      None

    FUNCTION:
      To print out a report using the OBJECTID list obtained from
      Get_AGOL_Object_Ids_Where() function.  Pass in a list of fields that you
      want reported and the script will print out the field and the fields value
      for each OBJECTID passed into this function.
    """
    print '--------------------------------------------------------------------'
    print 'Starting AGOL_Query_Features()'
    import urllib2, urllib, json


    # Turn the list of object_ids into one string with comma separated IDs,
    #   Then url encode it
    object_ids_str = ','.join(str(x) for x in object_ids)
    encoded_obj_ids = urllib.quote(object_ids_str)

    # Turn the list of required fields into one string with comma separations
    #   Then url encode it
    fields_to_report_str = ','.join(str(x) for x in fields_to_report)
    encoded_fields_to_rpt = urllib.quote(fields_to_report_str)

    print '  Querying Features in FS: "{}" and index "{}"'.format(name_of_FS, index_of_layer_in_FS)
    print '  OBJECTIDs to be queried: {}'.format(object_ids_str)
    print '  Fields to be reported on: {}'.format(fields_to_report_str)

    # Set URLs
    query_url = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/{}/query'.format(name_of_FS, index_of_layer_in_FS)
    query = '?where=&objectIds={}&outFields={}&returnGeometry=false&f=json&token={}'.format(encoded_obj_ids,encoded_fields_to_rpt, token)
    get_report_url = query_url + query
    ##print get_report_url

    # Get the report data and print
    response = urllib2.urlopen(get_report_url)
    response_json_obj = json.load(response)
    ##print response_json_obj

    # Print out a report for each field for each feature in the object_ids list
    print '\n  Reporting:'
    for feature in (response_json_obj['features']):
        for field in fields_to_report:
            print '    {}: {}'.format(field, feature['attributes'][field])
        print ''

    print 'Finished AGOL_Query_Features()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                FUNCTION:    Update AGOL Features

def AGOL_Update_Features(name_of_FS, index_of_layer_in_FS, object_id, field_to_update, new_value, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      index_of_layer_in_FS (int): The index of the layer in the Feature Service.
        This will frequently be 0, but it could be a higer number if the FS has
        multiple layers in it.
      object_id (str or int): OBJECTID that should be updated.
      field_to_update (str): Field in the FS that should be updated.
      new_value (str or int): New value that should go into the field.  Data
        type depends on the data type of the field.
      token (str): Token from AGOL that gives permission to interact with
        data stored on AGOL servers.  Obtained from the Get_Token().

    RETURNS:
      success (boolean): 'True' if there were no errors.  'False' if there were.

    FUNCTION:
      To Update features on an AGOL Feature Service.
    """

    print '--------------------------------------------------------------------'
    print "Starting AGOL_Update_Features()"
    import urllib2, urllib, json

    success = True

    # Set the json upate
    features_json = {"attributes" : {"objectid" : object_id, "{}".format(field_to_update) : "{}".format(new_value)}}
    ##print 'features_json:  {}'.format(features_json)

    # Set URLs
    update_url       = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/{}/updateFeatures?token={}'.format(name_of_FS, index_of_layer_in_FS, token)
    update_params    = urllib.urlencode({'Features': features_json, 'f':'json'})


    # Update the features
    print '  Updating Features in FS: {}'.format(name_of_FS)
    print '                 At index: {}'.format(index_of_layer_in_FS)
    print '   OBJECTID to be updated: {}'.format(object_id)
    print '      Field to be updated: {}'.format(field_to_update)
    print '   New value for updt fld: {}'.format(new_value)

    ##print update_url + update_params
    response  = urllib2.urlopen(update_url, update_params)
    response_json_obj = json.load(response)
    ##print response_json_obj

    for result in response_json_obj['updateResults']:
        ##print result
        print '    OBJECTID: {}'.format(result['objectId'])
        print '      Updated? {}'.format(result['success'])
        if result['success'] != True:
            success = False

    print 'Finished AGOL_Update_Features()\n'
    return success

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                 FUNCTION:  Unregister AGOL Replica IDs

def AGOL_Unregister_Replica_Ids(name_of_FS, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      token (str): Obtained from the Get_Token().

    RETURNS:
      None

    FUNCTION:
      To be used to get a list of replicas for an AGOL Feature Service and then
      ask the user if they wish to unregister the replicas that were listed.
      This will primarily be used to be allowed to overwrite an existing FS that
      has replicas from other users who have not removed a map from Collector.

    NOTE: This function assumes that you have obtained a Token with Get_Token()
    """
    print '--------------------------------------------------------------------'
    print 'Starting AGOL_Unregister_Replica_Ids()'
    import urllib2, urllib, json

    #---------------------------------------------------------------------------
    #              Get list of Replicas for the Feature Service

    # Set the URLs
    list_replica_url     = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/arcgis/rest/services/{}/FeatureServer/replicas'.format(name_of_FS)
    query                = '?f=json&token={}'.format(token)
    get_replica_list_url = list_replica_url + query
    ##print get_replica_list_url

    # Get the replicas
    print '  Getting replicas for: {}'.format(name_of_FS)
    response = urllib2.urlopen(get_replica_list_url)
    replica_json_obj = json.load(response)
    ##print replica_json_obj

    if len(replica_json_obj) == 0:
        print '  No replicas for this feature service.'
    else:
        #-----------------------------------------------------------------------
        #               Print out the replica ID and username owner
        for replica in replica_json_obj:
            print '  Replica: {}'.format(replica['replicaID'])

            list_replica_url = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/arcgis/rest/services/{}/FeatureServer/replicas/{}'.format(name_of_FS, replica['replicaID'])
            query            = '?f=json&token={}'.format(token)
            replica_url      = list_replica_url + query
            response = urllib2.urlopen(replica_url)
            owner_json_obj = json.load(response)
            print '  Is owned by: {}\n'.format(owner_json_obj['replicaOwner'])

        #-----------------------------------------------------------------------
        #                      Unregister Replicas
        # Ask user if they want to unregister the replicas mentioned above
        unregister_replicas = raw_input('Do you want to unregister the above replicas? (y/n)')

        if unregister_replicas == 'y':
            for replica in replica_json_obj:
                print '  Unregistering replica: {}'.format(replica['replicaID'])
                unregister_url = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/unRegisterReplica?token={}'.format(name_of_FS, token)
                unregister_params = urllib.urlencode({'replicaID': replica['replicaID'], 'f':'json'})

                response = urllib2.urlopen(unregister_url, unregister_params)
                unregister_json_obj = json.load(response)
                print '    Success: {}'.format(unregister_json_obj['success'])

    print 'Finished AGOL_Unregister_Replica_Ids()'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                                 FUNCTION Attach_File_to_Email
def Attach_File_To_Email(file_to_attach):
    """
    PARAMETERS:
      file_to_attach (str): Full path to an item to attach to an email.

    RETURNS:
      None

    FUNCTION:
      To attach a file (Excel, Word) to an email.

    NOTE:
      This function is NOT CURRENTLY WORKING.  It simply contains the logic that
      has been used in the past to attach Excel files to emails.
    """
### Import emailing modules
##from email.mime.multipart import MIMEMultipart
##from email.mime.application import MIMEApplication
##from email import encoders
##from email.message import Message
##from email.mime.text import MIMEText

##    msg = MIMEMultipart()
##    msg['Subject']   = subj
##    msg['From']      = "Python Script"
##    msg['To']        = ', '.join(email_list)  # Join each item in list with a ', '
##    msg.attach(MIMEText(body, 'html'))

##    # Set the attachment if needed
##    if (attach_excel_report == True):
##        attachment = MIMEApplication(open(file_to_attach, 'rb').read())
##
##        # Get name for attachment, which should equal the name of the file_to_attach
##        file_name = os.path.split(file_to_attach)[1]
##
##        # Set attachment into msg
##        attachment['Content-Disposition'] = 'attachment; filename = "{}"'.format(file_name)
##        msg.attach(attachment)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                        FUNCTION:  APPEND DATA

def Append_Data(input_item, target, schema_type, field_mapping=None):
    """
    PARAMETERS:
      input_item (str) = Full path to the item to append.
      target (str) = Full path to the item that will be updated.
      schema_type (str) = Controls if a schema test will take place.
      field_mapping {arcpy.FieldMappings obj} = Arcpy Field Mapping object.
        Optional.

    RETURNS:
      None

    FUNCTION:
      To append the data from the input_item to the target using an
      optional arcpy field_mapping object to override the default field mapping.
    """

    print '--------------------------------------------------------------------'
    print 'Appending Data...'
    print '  From: {}'.format(input_item)
    print '  To:   {}'.format(target)

    # If there is a field mapping object, make sure there is no schema test
    if field_mapping <> None:
        schema_type = 'NO_TEST'

    # Process
    arcpy.Append_management(input_item, target, schema_type, field_mapping)

    print 'Successfully appended data.\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         Function Backup Feature Class
def Backup_FC(full_path_to_fc):
    """
    PARAMETERS:
      full_path_to_fc (str): Full path to the FC you want to create a copy of.

    RETURNS:
      None

    FUNCTION:
      To create a copy of a FC.  Primarily as a Backup.  Appends '_BAK' to the
      end of the copied FC.  The FC is copied to the same workspace as the
      original FC.  The original FC remains unchanged.
    """

    arcpy.env.overwriteOutput = True
    import os

    print '--------------------------------------------------------------------'
    print 'Starting Backup_FC'


    in_features = full_path_to_fc
    out_path    = os.path.dirname(full_path_to_fc)
    out_name    = '{}_BAK'.format(os.path.basename(full_path_to_fc))

    print '  Backing up FC: {}'.format(in_features)
    print '             To: {}'.format(out_path)
    print '             As: {}'.format(out_name)

    arcpy.FeatureClassToFeatureClass_conversion (in_features, out_path, out_name)

    print 'Successfully Backed up FC\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       Function Check_For_Missing_Values()
def Check_For_Missing_Values(target_table, table_to_check, target_field, check_field, values_to_ignore, email_list, cfgFile):
    """
    PARAMETERS:
      target_table (str): Table to get the values to check.
      table_to_check (str): Table to perform the check on.
      target_field (str): Name of the field in the target_table to check.
      check_field (str): Name of the field in the table_to_check to perform the
        check on.
      values_to_ignore (str): List of Site Numbers in the Visits database
        that we should ignore in this function.  We would
        ignore these sites because there could be Visits to sites in the past
        for sites that were later deleted in the Sites database (and we do not
        want to get Warning emails for these).
      email_list(str): List of email addresses
      cfgFile (str): Path to a config file (.txt or .ini) with format:
        [email]
        usr: <username>
        pwd: <password>

    RETURNS:
      None

    FUNCTION:
      To check for any missing values from one field in one table when compared
      to a target table/field.  Sends an email if there are missing values
      in the table_to_check.
    """
    print 'Starting Check_For_Missing_Values()'
    print '  Target Table   = {}'.format(target_table)
    print '  Table To Check = {}'.format(table_to_check)
    print '  Target Field   = {}'.format(target_field)
    print '  Check Field    = {}'.format(check_field)
    if len(values_to_ignore) > 0:
        print '  Site Numbers in the Visit database to ignore:'
        for num in values_to_ignore:
            print '    {}'.format(str(num))
    print ''

    # Get list of unique values in the Table To Check
    print '  Getting list of unique values in the Table To Check'
    unique_values = []
    with arcpy.da.SearchCursor(table_to_check, [check_field]) as check_cursor:
        for row in check_cursor:
            value = row[0]
            if value not in unique_values:
                unique_values.append(value)

    del row, check_cursor
    unique_values.sort()
    ##print unique_values

    # Get list of values that ARE in Target Table that are NOT in Table To Check
    print '  Getting list of values in Target Table that are not in Table To Check'
    missing_values = []
    with arcpy.da.SearchCursor(target_table, [target_field]) as target_cursor:
        for row in target_cursor:
            value = row[0]
            if (value not in unique_values) and (value not in values_to_ignore) and (str(value) not in missing_values):
                missing_values.append(str(value))

    del row, target_cursor
    missing_values.sort()
    ##print missing_values

    if len(missing_values) > 0:  # Then there were missing values
        print '  There were values in Target Table that are not in Table To Check'
        for m_val in missing_values:
            print '    {}'.format(m_val)

        print '\n  Sending Warning Email...\n'

        missing_values_str = '<br>'.join(missing_values)

        subj = 'WARNING!  There were missing values in {}.'.format(check_field)
        body = """<enter warning in HTML format here>
        """.format(check_field, os.path.basename(table_to_check), missing_values_str)

        Email_W_Body(subj, body, email_list, cfgFile)

    else:
        print '  There were NO missing values in the Table To Check.  No Warning email needed.'

    print 'Finished Check_For_Missing_Values()'
    print '------------------------------------------------------------------\n'

    return


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         Function Check_For_Unique_Values
def Check_For_Unique_Values(table, field):
    """
    PARAMETERS:
      table (str): Full path to a FC or Table in a FGDB
      field (str): Name of a field in the above 'table'
      email_list(str): List of email addresses
      cfgFile (str): Path to a config file (.txt or .ini) with format:
        [email]
        usr: <username>
        pwd: <password>

    RETURNS:
      all_unique_values {boolean): True if all the values in the specified field
        are unique.  False if there is at least one duplicate.

    FUNCTION:
      To check a field in a table and see if there are any duplicate values in
      that field.
    """

    print 'Starting Check_For_Unique_Values()'
    print '  Checking field: "{}" in table: "{}"'.format(field, table)

    unique_values    = []
    duplicate_values = []
    all_unique_values = True

    with arcpy.da.SearchCursor(table, [field]) as cursor:
        for row in cursor:
            value = row[0]
            if value not in unique_values:
                unique_values.append(value)
            else:
                duplicate_values.append(value)
                all_unique_values = False

    if len(duplicate_values) > 0:
        print '  There were duplicate values:'
        for duplicate_value in duplicate_values:
            print '    {}'.format(duplicate_value)

    else:
        print '  There were NO duplicate values'

    print 'Finished Check_For_Unique_Values()\n'

    return all_unique_values

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Copy_Directory(src, dest):
    """
    PARAMETERS:
      src (str): Path to a folder that you want to create a copy of (including
        the files and folder structure).
      dest (str): Path to a folder that will contain the copied folder from
        'src' above.

    RETURNS:
      None

    FUNCTION:
      To create a copy of a folder from the 'src' to the 'dest' folder.  The
        The copied folder (along with all the files and folder structure) will
        be copied to the 'dest' folder.  The new folder will be given the name
        of the 'src' folder with the 'YYYY_MM_DD__HH_MM_SS' appended to it.

    NOTE:
      This function assumes that the Get_DT_To_Append() is available to use.
    """

    import errno, shutil
    print '\n------------------------------------------------------------------'
    print 'Starting Copy_Directory()'

    name_of_backup = os.path.basename(src)  # Get the name of the folder that is being backed up
    dt_to_append = Get_DT_To_Append()   # Get the current date and time the folder is being backed up
    path_and_name_of_backup = os.path.join(dest, name_of_backup + '_' + dt_to_append)

    print '  Copying Directory from: "{}"'.format(src)
    print '                      To: "{}"'.format(path_and_name_of_backup)

    try:
        shutil.copytree(src, path_and_name_of_backup, ignore=shutil.ignore_patterns('*.lock'))
        print ' '
    except OSError as e:
        # If the error was caused because the source wasn't a directory
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, path_and_name_of_backup)  # Then copy the file
        else:
            print('*** Directory not copied. Error: %s ***' % e)

    print 'Finished Copy_Directory()'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                                 FUNCTION Copy_Features()
def Copy_Features(in_FC, out_FC):
    """
    PARAMETERS:
      in_FC (str): Full path to an input feature class.
      out_FC (str): Full path to an existing output feature class.

    RETURNS:
      None

    FUNCTION:
      To copy the features from one feature class to another existing
      feature class.
    """

    print 'Starting Copy_Features()...'

    print '  Copying Features from: "{}"'.format(in_FC)
    print '                     To: "{}"'.format(out_FC)

    arcpy.CopyFeatures_management(in_FC, out_FC)

    print 'Finished Copy_Features()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                                 FUNCTION Copy_Rows()
def Copy_Rows(in_table, out_table):
    """
    PARAMETERS:
      in_table (str): Full path to an input table.
      out_table (str): Full path to an existing output table.

    RETURNS:
      None

    FUNCTION:
      To copy the rows from one table to another table.
    """

    print 'Starting Copy_Rows()...'

    print '  Copying Rows from: "{}"'.format(in_table)
    print '                 To: "{}"'.format(out_table)

    arcpy.CopyRows_management(in_table, out_table)

    print 'Finished Copy_Rows()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                           FUNCTION Create_FGDB()
def Create_FGDB(path_name_FGDB, overwrite_if_exists=False):
    """
    PARAMETERS:

    RETURNS:

    FUNCTION:
    """

    print 'Starting Create_FGDB()...'

    path, name = os.path.split(path_name_FGDB)

    #---------------------------------------------------------------------------
    #          Set create_fgdb variable to control if process is run

    # If FGDB doesn't exist, create it
    if not os.path.exists(path_name_FGDB + '.gdb'):
        create_fgdb = True

    # If FGDB does exist...
    else:
        # ... and overwrite_if_exists == True, create it
        if overwrite_if_exists == True:
            create_fgdb = True

        # ... and overwrite_if_exists == False, do not create FGDB
        else:
            create_fgdb = False

    #---------------------------------------------------------------------------
    # Run process if create_fgdb == True
    if create_fgdb == True:
        print '  Creating FGDB: "{}" at: "{}"'.format(name, path)
        arcpy.CreateFileGDB_management(path, name, 'CURRENT')

    else:
        print '  FGDB not created.  Set "overwrite_if_exists" to "True"'

    print 'Finished Create_FGDB()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Delete_Features()
def Delete_Features(in_fc):
    """
    PARAMETERS:
      in_fc (str): Full path to a Feature Class.

    RETURNS:
      None

    FUNCTION:
      To delete the features from one FC.
    """

    print '--------------------------------------------------------------------'
    print 'Starting Delete_Features()...'

    print '  Deleting Features from: "{}"'.format(in_fc)

    arcpy.DeleteFeatures_management(in_fc)

    print 'Finished Delete_Features()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                                 FUNCTION Delete_Rows()
def Delete_Rows(in_table):
    """
    PARAMETERS:
      in_table (str): Full path to a table.

    RETURNS:
      None

    FUNCTION:
      To delete the rows from one table.
    """

    print 'Starting Delete_Rows()...'

    print '  Deleting Rows from: "{}"'.format(in_table)

    arcpy.DeleteRows_management(in_table)

    print 'Finished Delete_Rows()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#            FUNCTION: Export DPW_WP_SITES to Survey123's Site_Info csv
def DPW_WP_SITES_To_Survey123_csv(Sites_Export_To_CSV_tbl, DPW_WP_SITES, Site_Info):
    """
    NOTE: This function is from DPW_Science_and_Monitoring.py, but is no longer
    being used in that script.

    PARAMETERS:

    RETURNS:

    FUNCTION:
    """
    print '--------------------------------------------------------------------'
    print 'Exporting Sites Data to the Survey123 CSV...'

    # Sites_Export_To_CSV is a table that has the same schema the CSV needs in
    # order to work with Survey123.

    #---------------------------------------------------------------------------
    #               Delete rows in Sites_Export_To_CSV FGDB table

    print '  Deleting Rows in: {}'.format(Sites_Export_To_CSV_tbl)

    arcpy.DeleteRows_management(Sites_Export_To_CSV_tbl)

    #---------------------------------------------------------------------------
    #         Export prod DPW_WP_SITES to a working table in the working_FGDB

    working_FGDB = os.path.split(Sites_Export_To_CSV_tbl)[0]  # Get the working FGDB path
    DPW_WP_SITES_tbl = 'D_SITES_exported_tbl'
    DPW_WP_SITES_tbl_path = working_FGDB + '\\' + DPW_WP_SITES_tbl

    print '  Exporting DPW_WP_SITES to a working table:'
    print '    From: {}'.format(DPW_WP_SITES)
    print '    To:   {}'.format(DPW_WP_SITES_tbl_path)

    arcpy.TableToTable_conversion(DPW_WP_SITES, working_FGDB, DPW_WP_SITES_tbl)

    #---------------------------------------------------------------------------
    #            Append DPW_WP_SITES_tbl to the Sites_Export_To_CSV table

    inputs = working_FGDB + '\\' + DPW_WP_SITES_tbl

    print '  Appending {}'.format(DPW_WP_SITES_tbl)
    print '    From: {}'.format(inputs)
    print '    To:   {}'.format(Sites_Export_To_CSV_tbl)

    arcpy.Append_management(inputs, Sites_Export_To_CSV_tbl, 'TEST')

    #---------------------------------------------------------------------------
    #                         Field Calculations
    # Some field calculations have to be performed on the Sites_Export_To_CSV_tbl
    # in order that the comma and quote sensitive Survey123 app can read it correctly

    # Do a search for ',' and replace with a ' ' to make sure no commas get into
    #  the CSV file in the Loc_Desc field
    field = 'Loc_Desc'
    expression = '!Loc_Desc!.replace(",", " ")'
    expression_type = "PYTHON_9.3"

    print '  Calculating field: {}, so that it equals: {}'.format(field, expression)

    arcpy.CalculateField_management(Sites_Export_To_CSV_tbl, field, expression, expression_type)

    # Do a search for a quote (") and replace with an 'in.' to make sure no quotes get into
    #  the CSV file in the Loc_Desc field
    ##print '  Replacing \" with an \'in.\' in Loc_Desc field'
    field = 'Loc_Desc'
    expression = "!Loc_Desc!.replace('\"', 'in.')"
    expression_type = "PYTHON_9.3"

    print '  Calculating field: {}, so that it equals: {}'.format(field, expression)

    arcpy.CalculateField_management(Sites_Export_To_CSV_tbl, field, expression, expression_type)

    #---------------------------------------------------------------------------
    #                      Export to CSV and clean up files.

    out_path = os.path.split(Site_Info)[0]  # Get the Path
    out_name = os.path.split(Site_Info)[1]  # Get the file name

    print '  Exporting to CSV'
    print '    From: {}'.format(Sites_Export_To_CSV_tbl)
    print '    To:   {}'.format(Site_Info)

    arcpy.TableToTable_conversion(Sites_Export_To_CSV_tbl, out_path, out_name)

    # Delete the extra files that are not needed that are created by the above export
    print '  Deleting extra files auto-generated by export process.'
    schema_file = out_path + '\\schema.ini'
    xml_file = out_path + '\\Site_Info.txt.xml'
    if os.path.exists(schema_file):
        os.remove(schema_file)
    if os.path.exists(xml_file):
        os.remove(xml_file)

    print 'Successfully exported DPW_WP_SITES to Survey123 CSV\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                               Function Email_W_Body()
def Email_W_Body(subj, body, email_list, cfgFile=
    r"P:\DPW_ScienceAndMonitoring\Scripts\DEV\DEV_branch\Control_Files\accounts.txt"):

    """
    PARAMETERS:
      subj (str): Subject of the email
      body (str): Body of the email in HTML.  Can be a simple string, but you
        can use HTML markup like <b>bold</b>, <i>italic</i>, <br>carriage return
        <h1>Header 1</h1>, etc.
      email_list (str): List of strings that contains the email addresses to
        send the email to.
      cfgFile {str}: Path to a config file with username and password.
        The format of the config file should be as below with
        <username> and <password> completed:

          [email]
          usr: <username>
          pwd: <password>

        OPTIONAL. A default will be used if one isn't given.

    RETURNS:
      None

    FUNCTION: To send an email to the listed recipients.
      If you want to provide a log file to include in the body of the email,
      please use function Email_w_LogFile()
    """
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import ConfigParser, smtplib

    print 'Starting Email_W_Body()'

    # Set the subj, From, To, and body
    msg = MIMEMultipart()
    msg['Subject']   = subj
    msg['From']      = "Python Script"
    msg['To']        = ', '.join(email_list)  # Join each item in list with a ', '
    msg.attach(MIMEText(body, 'html'))

    # Get username and password from cfgFile
    config = ConfigParser.ConfigParser()
    config.read(cfgFile)
    email_usr = config.get('email', 'usr')
    email_pwd = config.get('email', 'pwd')

    # Send the email
    ##print '  Sending the email to:  {}'.format(', '.join(email_list))
    SMTP_obj = smtplib.SMTP('smtp.gmail.com',587)
    SMTP_obj.starttls()
    SMTP_obj.login(email_usr, email_pwd)
    SMTP_obj.sendmail(email_usr, email_list, msg.as_string())
    SMTP_obj.quit()
    time.sleep(2)

    print 'Finished Email_W_Body().'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION Email_W_LogFile()
def Email_W_LogFile(email_subject, email_recipients, email_login_info, log_file=None):
    """
    PARAMETERS:
      email_subject (str): The subject line for the email

      email_recipients (list): List (of strings) of email addresses

      email_login_info (str): Path to a config file with username and password.
        The format of the config file should be as below with
        <username> and <password> completed:

          [email]
          usr: <username>
          pwd: <password>


      log_file {str}: Path to a log file to be included in the body of the
        email. Optional.


    RETURNS:
      None


    FUNCTION:
      To send an email to the listed recipients.  May provide a log file to
      include in the body of the email.
    """

    import smtplib, ConfigParser
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    print 'Starting Email()'

    # Set log file into body of email if provided
    if log_file != None:
        # Get the log file to add to email body
        fp = open(log_file,"rb")
        msg = MIMEText(fp.read())
        fp.close()
    else:
        msg = MIMEMultipart()

    # Get username and pwd from the config file
    try:
        config = ConfigParser.ConfigParser()
        config.read(email_login_info)
        email_usr = config.get("email","usr")
        email_pwd = config.get("email","pwd")
    except:
        print 'ERROR!  Could not read config file.  May not exist at location, or key may be incorrect.  Email not sent.'
        return

    # Set from and to addresses
    fromaddr = "dplugis@gmail.com"
    toaddr = email_recipients
    email_recipients_str = ', '.join(email_recipients)  # Join each item in list with a ', '

    # Set visible info in email
    msg['Subject'] = email_subject
    msg['From']    = "Python Script"
    msg['To']      = email_recipients_str

    # Email
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(email_usr,email_pwd)
    s.sendmail(fromaddr,toaddr,msg.as_string())
    s.quit()

    print 'Sent email with subject "{}"'.format(email_subject)
    print 'To: {}'.format(email_recipients_str)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION Excel_To_Table()
def Excel_To_Table(input_excel_file, out_table, sheet):
    """
    PARAMETERS:
        input_excel_file (str): The full path to the Excel file to import.

        out_table (str): The full path to the FGDB and NAME of the table in the FGDB.

        sheet (str): The name of the sheet to import.

    RETURNS:
        none

    FUNCTION:
        To import an Excel sheet into a FGDB.
    """

    print 'Starting Excel_To_Table()...'

    print '  Importing Excel file: {}\{}\n  To: {}'.format(input_excel_file, sheet, out_table)

    # Perform conversion
    arcpy.ExcelToTable_conversion(input_excel_file, out_table, sheet)

    print 'Finished Excel_To_Table()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION:   Export to Excel
def Export_To_Excel(wkg_folder, wkg_FGDB, table_to_export, export_folder, dt_to_append, report_TMDL_csv):
    """
    NOTE: This function is from DPW_Science_and_Monitoring.py, but is no longer
    being used in that script.

    PARAMETERS:

    RETURNS:

    FUNCTION:
      Exports the production DPW_WP_FIELD_DATA table to a working table, deletes the
      unneeded fields in the working table and then exports that table to excel.
      Essentially creating a 'Report' in Excel based on the where_clause.
    """
    print '--------------------------------------------------------------------'
    print 'Exporting to Excel...'


    #---------------------------------------------------------------------------
    #            Export table_to_export to wkg_FGDB to delete fields
    out_path     = wkg_folder + '\\' + wkg_FGDB
    out_name     = 'Report__Bacteria_TMDL_Outfall'
    where_clause = "Project = 'Bacteria TMDL Outfalls'"

    wkg_table = out_path + '\\' + out_name
    print '  Exporting table to table:'
    print '    From:  {}'.format(table_to_export)
    print '    To:    {}'.format(wkg_table)
    print '    Where: {}'.format(where_clause)

    arcpy.TableToTable_conversion(table_to_export, out_path, out_name, where_clause)


    #---------------------------------------------------------------------------
    #              Delete fields that are not needed/wanted in report

    with open (report_TMDL_csv) as csv_file:
        readCSV = csv.reader(csv_file, delimiter = ',')

        fields_to_delete = []

        row_num = 0
        for row in readCSV:
            if row_num > 1:
                f_to_delete = row[0]

                fields_to_delete.append(f_to_delete)
            row_num += 1

    num_deletes = len(fields_to_delete)

    print '  There are {} fields to delete:'.format(num_deletes)

    # If there is at least one field to delete, delete it
    if num_deletes > 0:
        f_counter = 0
        while f_counter < num_deletes:
            drop_field = fields_to_delete[f_counter]
            ##print '    Deleting field: %s...' % drop_field

            arcpy.DeleteField_management(wkg_table, drop_field)

            f_counter += 1
    print '  Fields deleted.'

    #---------------------------------------------------------------------------
    #                            Export table to Excel

    # Make the export file if it doesn't exist
    if not os.path.exists(export_folder):
        os.mkdir(export_folder)

    export_file = export_folder + '\\Bacteria_TMDL_Report_{}.xls'.format(dt_to_append)

    print '  Exporting table to Excel...'
    print '    From: ' + wkg_table
    print '    To :  ' + export_file

    # Process
    arcpy.TableToExcel_conversion(wkg_table, export_file, 'ALIAS')

    print 'Successfully exported database to Excel.\n'

    return export_file

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         FUNCTION: Extract Parcels
def Extract_Parcels(parcels_all, related_fc, parcels_int_related_fc):
    """
    PARAMETERS:
      parcels_all (str): Full path to the PARCELS_ALL FC.  This should be an SDE
        FC.

      related_fc (str):  Full path to a FC that will be used to select parcels
        that intersect features in this FC.

      parcels_int_related_fc (str):  Full path to an EXISTING FC that will contain
        the selected parcels.

    RETURNS:
      None

    FUNCTION:
      To select the parcels that intersect the 'related_fc' features and then
      appending the selected parcels into the the 'parcels_int_related_fc'.

      This function is usually used to speed up other geoprocessing tasks that
      may be performed on a parcels database.

      NOTE: This function deletes the existing features in the
        'parcels_int_related_fc' before appending the selected parcels so we get
        a 'fresh' FC each run of the script AND there is no schema lock to worry
        about.
    """

    print '--------------------------------------------------------------------'
    print 'Starting Extract_Parcels()'

    print '  PARCELS_ALL FC path:\n    {}'.format(parcels_all)
    print '  Related FC used to select parcels:\n    {}'.format(related_fc)

    # Delete the existing features
    print '  Deleting the old existing parcels at:\n    {}'.format(parcels_int_related_fc)
    arcpy.DeleteFeatures_management(parcels_int_related_fc)

    # Make a feature layer out of the PARCELS_ALL FC
    arcpy.MakeFeatureLayer_management(parcels_all, 'par_all_lyr')

    # Select Parcels that intersect with the DA Reports
    print '\n  Selecting parcels that intersect with the DA Reports'
    arcpy.SelectLayerByLocation_management('par_all_lyr', 'INTERSECT', related_fc)

    # Get count of selected parcels
    count = Get_Count_Selected('par_all_lyr')
    print '  There are: "{}" selected parcels\n'.format(count)

    # Export selected parcels
    if (count != 0):

        # Append the newly selected features
        print '  Appending the selected parcels to:\n    {}'.format(parcels_int_related_fc)
        arcpy.Append_management('par_all_lyr', parcels_int_related_fc, 'NO_TEST')

    else:
        print '*** WARNING! There were no selected parcels. ***'
        print '  Please find out why there were no selected parcels.'
        print '  Script still allowed to run w/o an error flag.'

    print 'Finished Extract_Parcels()\n'

    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                        FUNCTION: ADD FIELDS

def Fields_Add_Fields(wkg_data, add_fields_csv):
    """
    PARAMETERS:
      wkg_data (str) = Name of the working FC in the wkgGDB. This is the FC
        that is processed.
      add_fields_csv (str) = Full path to the CSV file that lists which fields
        should be created.

    RETURNS:
      None

    FUNCTION:
      To add fields to the wkg_data using a CSV file located at add_fields_csv.
    """
    import csv

    print '--------------------------------------------------------------------'
    print 'Adding fields to:\n  %s' % wkg_data
    print '  Using Control CSV at:\n    {}\n'.format(add_fields_csv)
    with open (add_fields_csv) as csv_file:
        readCSV = csv.reader(csv_file, delimiter = ',')

        # Create blank lists
        f_names = []
        f_types = []
        f_lengths = []

        row_num = 0
        for row in readCSV:
            if row_num > 1:
                f_name   = row[0]
                f_type   = row[1]
                f_length = row[2]

                f_names.append(f_name)
                f_types.append(f_type)
                f_lengths.append(f_length)
            row_num += 1

    num_new_fs = len(f_names)
    print '    There are %s new fields to add:' % str(num_new_fs)

    f_counter = 0
    while f_counter < num_new_fs:
        print ('      Creating field: %s, with a type of: %s, and a length of: %s'
        % (f_names[f_counter], f_types[f_counter], f_lengths[f_counter]))

        in_table          = wkg_data
        field_name        = f_names[f_counter]
        field_type        = f_types[f_counter]
        field_precision   = '#'
        field_scale       = '#'
        field_length      = f_lengths[f_counter]
        field_alias       = '#'
        field_is_nullable = '#'
        field_is_required = '#'
        field_domain      = '#'


        try:
            # Process
            arcpy.AddField_management(in_table, field_name, field_type,
                        field_precision, field_scale, field_length, field_alias,
                        field_is_nullable, field_is_required, field_domain)
        except Exception as e:
            print '*** WARNING! Field: %s was not able to be added.***' % field_name
            print str(e)
        f_counter += 1

    print 'Successfully added fields.\n'

    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                     FUNCTION: CALCULATE FIELDS

def Fields_Calculate_Fields(wkg_data, calc_fields_csv):
    """
    PARAMETERS:
      wkg_data (str) = Name of the working FC in the wkgGDB. This is the FC
        that is processed.
      calc_fields_csv (str) = Full path to the CSV file that lists which fields
        should be calculated, and how they should be calculated.

    RETURNS:
      None

    FUNCTION:
      To calculate fields in the wkg_data using a CSV file located at
      calc_fields_csv.
    """
    import csv

    print '--------------------------------------------------------------------'
    print 'Calculating fields in:\n  %s' % wkg_data
    print '  Using Control CSV at:\n    {}\n'.format(calc_fields_csv)

    # Make a table view so we can perform selections
    arcpy.MakeTableView_management(wkg_data, 'wkg_data_view')

    #---------------------------------------------------------------------------
    #                   Get values from the CSV file:
    #                FieldsToCalculate.csv (calc_fields_csv)
    with open (calc_fields_csv) as csv_file:
        readCSV = csv.reader(csv_file, delimiter = ',')

        where_clauses = []
        calc_fields = []
        calcs = []

        row_num = 0
        for row in readCSV:
            if row_num > 1:
                where_clause = row[0]
                calc_field   = row[2]
                calc         = row[4]

                where_clauses.append(where_clause)
                calc_fields.append(calc_field)
                calcs.append(calc)
            row_num += 1

    num_calcs = len(where_clauses)
    print '    There are %s calculations to perform:\n' % str(num_calcs)

    #---------------------------------------------------------------------------
    #                    Select features and calculate them
    f_counter = 0
    while f_counter < num_calcs:
        #-----------------------------------------------------------------------
        #               Select features using the where clause

        in_layer_or_view = 'wkg_data_view'
        selection_type   = 'NEW_SELECTION'
        my_where_clause  = where_clauses[f_counter]

        print '      Selecting features where: "%s"' % my_where_clause

        # Process
        arcpy.SelectLayerByAttribute_management(in_layer_or_view, selection_type, my_where_clause)

        #-----------------------------------------------------------------------
        #     If features selected, perform one of the following calculations
        # The calculation that needs to be performed depends on the field or the calc
        #    See the options below:

        countOfSelected = arcpy.GetCount_management(in_layer_or_view)
        count = int(countOfSelected.getOutput(0))
        print '        There was/were %s feature(s) selected.' % str(count)

        if count != 0:
            in_table   = in_layer_or_view
            field      = calc_fields[f_counter]
            calc       = calcs[f_counter]

            #-------------------------------------------------------------------
            # Test if the user wants to calculate the field being equal to
            # ANOTHER FIELD by seeing if the calculation starts or ends with an '!'
            if (calc.startswith('!') or calc.endswith('!')):
                f_expression = calc

                try:
                    # Process
                    arcpy.CalculateField_management(in_table, field, f_expression, expression_type="PYTHON_9.3")

                    print ('        From selected features, calculated field: %s, so that it equals FIELD: %s\n'
                            % (field, f_expression))

                except Exception as e:
                    print '*** WARNING! Field: %s was not able to be calculated.***\n' % field
                    print str(e)

            #-------------------------------------------------------------------
            # If calc does not start or end with a '!', it is probably because the
            # user wanted to calculate the field being equal to a STRING
            else:
                s_expression = "'%s'" % calc

                try:
                    # Process
                    arcpy.CalculateField_management(in_table, field, s_expression, expression_type="PYTHON_9.3")

                    print ('        From selected features, calculated field: %s, so that it equals STRING: %s\n'
                            % (field, s_expression))

                except Exception as e:
                    print '*** WARNING! Field: %s was not able to be calculated.***\n' % field
                    print str(e)

        else:
            print ('        WARNING.  No records were selected.  Did not perform calculation.\n')

        #-----------------------------------------------------------------------

        # Clear selection before looping back through to the next selection
        arcpy.SelectLayerByAttribute_management(in_layer_or_view, 'CLEAR_SELECTION')

        f_counter += 1

    print 'Successfully calculated fields.\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION DELETE FIELDS
def Fields_Delete_Fields(wkg_data, delete_fields_csv):
    """
    PARAMETERS:
      wkg_data (str) = Name of the working FC in the wkgGDB. This is the FC
        that is processed.  It is overwritten each time the script is run.
      delete_fields_csv (str) = Full path to the CSV file that lists which
        fields should be deleted.

    RETURNS:
      None

    FUNCTION:
      To delete fields from the wkg_data using a CSV file located at
      delete_fields_csv.
    """

    print '--------------------------------------------------------------------'
    print 'Deleting fields in:\n    %s' % wkg_data
    print '  Using Control CSV at:\n    {}\n'.format(delete_fields_csv)

    #---------------------------------------------------------------------------
    #                     Get values from the CSV file
    with open (delete_fields_csv) as csv_file:
        readCSV  = csv.reader(csv_file, delimiter = ',')

        delete_fields = []

        row_num = 0
        for row in readCSV:
            if row_num > 1:
                delete_field = row[0]
                delete_fields.append(delete_field)
            row_num += 1

    num_calcs = len(delete_fields)
    print '    There is/are %s deletion(s) to perform.\n' % str(num_calcs)

    #---------------------------------------------------------------------------
    #                          Delete fields

    # If there is at least one field to delete, delete it
    if num_calcs > 0:
        f_counter = 0
        while f_counter < num_calcs:
            drop_field = delete_fields[f_counter]
            print '    Deleting field: %s...' % drop_field

            arcpy.DeleteField_management(wkg_data, drop_field)

            f_counter += 1

        print 'Successfully deleted fields.\n'

    else:
        print 'WARNING.  NO fields were deleted.'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                           FUNCTION: GET FIELD MAPPINGS
def Fields_Get_Field_Mappings(orig_table, prod_table, map_fields_csv):
    """
    PARAMETERS:
      orig_table (str): Full path to the converted TABLE (from the working FC).
      prod_table (str): Full path to the production TABLE that contains the
        most up-to-date data.
      map_fields_csv (str): Full path to the CSV file that lists which fields
        in the converted TABLE match the fields in the production TABLE.

    RETURNS:
      fms (arcpy.FieldMappings object): This object contains the field mappings
        that can be used when we append the working data to the production data.

    FUNCTION:
      By using a CSV file that lists fields in the working data and their
      matching field in the production data, this function gets any non-default
      field mappings between the working data and the production data. The
      field mapping object is returned by the function so it can be used in an
      append function.

    NOTE:
      This function is only useful if there are any field names that are
      different between the working database and the production database.
      This is because the default for an append function is to match the field
      names between the target dataset and the appending dataset.
    """

    print '--------------------------------------------------------------------'
    print 'Getting Field Mappings...'

    #---------------------------------------------------------------------------
    #                      Get values from the CSV file
    with open (map_fields_csv) as csv_file:
        readCSV = csv.reader(csv_file, delimiter = ',')

        # Create blank lists
        orig_fields = []
        prod_fields = []

        row_num = 0
        for row in readCSV:
            if row_num > 1:
                # Get values for that row
                orig_field = row[0]
                prod_field = row[1]

                orig_fields.append(orig_field)
                prod_fields.append(prod_field)

            row_num += 1

    num_fm = len(orig_fields)
    print '  There are %s non-default fields to map.' % str(num_fm)

    #---------------------------------------------------------------------------
    #           Set the Field Maps into the Field Mapping object
    # Create FieldMappings obj
    fms = arcpy.FieldMappings()

    # Add the schema of the production table so that all fields that are exactly
    # the same name between the orig table and the prod table will be mapped
    # to each other by default
    fms.addTable(prod_table)

    # Loop through each pair of listed fields (orig and prod) and add the
    # FieldMap object to the FieldMappings obj
    counter = 0
    while counter < num_fm:
        print ('  Mapping Orig Field: "%s" to Prod Field: "%s"'
                                 % (orig_fields[counter], prod_fields[counter]))
        # Create FieldMap
        fm = arcpy.FieldMap()

        # Add the input field
        fm.addInputField(orig_table, orig_fields[counter])

        # Add the output field
        out_field_obj = fm.outputField
        out_field_obj.name = prod_fields[counter]
        fm.outputField = out_field_obj

        # Add the FieldMap to the FieldMappings
        fms.addFieldMap(fm)

        del fm
        counter += 1

    print 'Successfully Got Field Mappings\n'
    return fms

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                        FUNCTION Get_Count_Selected()
def Get_Count_Selected(lyr):
    """
    PARAMETERS:
      lyr (lyr): The layer that should have a selection on it that we want to test.

    RETURNS:
      count_selected (int): The number of selected records in the lyr

    FUNCTION:
      To get the count of the number of selected records in the lyr.
    """

    print 'Starting Get_Count()...'

    # See if there are any selected records
    desc = arcpy.Describe(lyr)

    if desc.fidSet: # True if there are selected records
        result = arcpy.GetCount_management(lyr)
        count_selected = int(result.getOutput(0))

    # If there weren't any selected records
    else:
        count_selected = 0

    print '  Count of Selected: {}'.format(str(count_selected))

    print 'Finished Get_Count()\n'

    return count_selected

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                                 FUNCTION Get_Dataset_Type()
def Get_Dataset_Type(in_item):
    """
    PARAMETERS:
      in_item (str): Full path to an item to get its dataset type.

    RETURNS:
      dataset_type (str): The dataset type of the item.  Common results include:
        'FeatureClass'
        'Table'
        'GeometricNetwork'
        'RasterDataset'

    FUNCTION:
      To get the dataset type of the 'in_item' and return a string describing
      the type of dataset.  Used when the main() may want to treat the item
      differently based on the dataset type.

      For example:
        A 'Table' may require an        'arcpy.CopyRows_management()' while,
        A 'FeatureClass' may require an 'arcpy.CopyFeatures_management()'
    """

    print 'Starting Get_Dataset_Type()...'
    print '  Getting Dataset Type of: "{}"'.format(in_item)

    desc = arcpy.Describe(in_item)
    dataset_type = desc.datasetType

    print '    "{}"'.format(dataset_type)
    print 'Finished Get_Dataset_Type\n'

    return dataset_type

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Get_dt_to_append
def Get_DT_To_Append():
    """
    PARAMETERS:
      none

    RETURNS:
      dt_to_append (str): Which is in the format 'YYYY_MM_DD__HH_MM_SS'

    FUNCTION:
      To get a formatted datetime string that can be used to append to files
      to keep them unique.
    """
    print 'Starting Get_DT_To_Append()...'

    start_time = datetime.datetime.now()

    date = start_time.strftime('%Y_%m_%d')
    time = start_time.strftime('%H_%M_%S')

    dt_to_append = '%s__%s' % (date, time)

    print '  DateTime to append: {}'.format(dt_to_append)

    print 'Finished Get_DT_To_Append()\n'
    return dt_to_append

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION: Get_List_Of_Parcels
def Get_List_Of_Parcels(rmaTrack, parcel_fc, roadBufferVal):
    """
    FUNCTION:
      Specific Function for a RMA Script
    """

    # Make feature layers needed below
    arcpy.MakeFeatureLayer_management(rmaTrack, 'rmaTrackLyr')
    arcpy.MakeFeatureLayer_management(parcel_fc,  'parcel_fcLyr')


    # Create a cursor to loop through all features in rmaTrack
    with arcpy.da.SearchCursor(rmaTrack, ['OBJECTID']) as trackCursor:
        for row in trackCursor:
            where_clause = "OBJECTID = {}".format(str(row[0])) # Select track by OBJECTID
            print 'Selecting where: ' + where_clause
            arcpy.SelectLayerByAttribute_management('rmaTrackLyr', 'NEW_SELECTION', where_clause)

            # Confirm one track was selected
            numfeats = arcpy.GetCount_management("rmaTrackLyr")
            count = int(numfeats.getOutput(0))
            ##print 'Count: ' + str(count)
            if count == 1:

                # Select parcels by location based on the selected track
                arcpy.SelectLayerByLocation_management('parcel_fcLyr', 'WITHIN_A_DISTANCE', 'rmaTrackLyr', roadBufferVal, 'NEW_SELECTION')

                # Confirm at least one parcel was selected
                numfeats = arcpy.GetCount_management("parcel_fcLyr")
                count = numfeats.getOutput(0)
                print 'Number of selected parcels: ' + str(count)
                if count > 0:

                    # Get a list of ALL the PARCELID's of the selected parcels
                    # Use PARCELID so we don't count 'stacked' parcels,
                    # but only parcel footprints.
                    parcel_ids = []
                    with arcpy.da.SearchCursor('parcel_fcLyr', ['PARCELID']) as parcelCursor:
                        for row in parcelCursor:
                            parcel_ids.append(row[0])

                    # Get a list of all the UNIQUE PARCELID's
                    # set() returns a list of only unique values
                    unique_parcel_ids = sorted(set(parcel_ids))
                    num_unique_parcel_ids = len(unique_parcel_ids)
                    print 'Number of PARCELID\'s: {}'.format(str(num_unique_parcel_ids))

                    # Calculate the PARCEL field in rmaTrack as the number of unique parcel ids
                    # Only the selected feature in rmaTrack will have it's field calculated.
                    arcpy.CalculateField_management('rmaTrackLyr', 'PARCELS', num_unique_parcel_ids, 'PYTHON_9.3')



            print ''

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         FUNCTION: Get Newest Data
def Get_Newest_Data(FGDB_path):
    """
    PARAMETERS:
      FGDB_path (str): Full path to a FGDB that contains the data to be searched.
        Data in this FGDB must contain FC's that are all named the same with the
        only difference between the FC's is that their time stamp is different.
        See below for info about the timestamp naming convention.

    RETURNS:
      newest_download_path(str): Full path to a FC that contains the newest
        downloaded data.

    FUNCTION:
      To return the full path of the FC containing the newest data.
      This works if the FGDB being searched only contains one FC basename and
      that FC is time stamped as 'YYYY_MM_DD__HH_MM_SS'.
      This ensures that the newest data will be the first FC in the list
      (because we do a reverse sort based on the name of the FC).

      For example:
        Data_From_AGOL_2018_01_01__10_00_00
        Data_From_AGOL_2018_01_02__10_00_00
        Data_From_AGOL_2018_01_02__10_00_01
    """

    print '--------------------------------------------------------------------'
    print 'Starting Get_Newest_Data()'

    arcpy.env.workspace = FGDB_path
    print 'Finding the newest data in: {}'.format(FGDB_path)

    # List all FC's in the FGDB
    AGOL_downloads = arcpy.ListFeatureClasses()

    # Sort the FC's alphabetically in reverse (this ensures the most recent date is first)
    AGOL_downloads.sort(reverse=True)
    newest_download = AGOL_downloads[0]

    # Set the path of the newest data
    newest_download_path = '{}\{}'.format(FGDB_path, newest_download)
    print 'The newest download is at:\n  {}'.format(newest_download_path)

    print 'Finished Get_Newest_Data()\n'

    return newest_download_path

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#               FUNCTION: Join DA Reports with Parcels Extract
def Join_2_FC_By_Spatial_Join(target_fc, join_fc, output_FGDB):
    """
    PARAMETERS:
      target_fc (str): Full path to the FC you want to be joined
        to the join_fc.  These are the features you want to add data TO.

      join_fc (str): Full path to the FC that holds the data
        you want to get information FROM.

      output_FGDB (str): Path to the FGDB that you want to hold the newly created joined FC.
        The full path to the FC in this FGDB will be calculated to be the path
        of this FGDB + the name of the target_fc + '_joined'

    RETURNS:
      output_fc (str): Full path to the FC that resulted from the spatial join

    FUNCTION:
      To spatially join the tabular information from the join_fc to the target_fc.
    """

    print '--------------------------------------------------------------------'
    print 'Starting Join_2_FC_By_Spatial_Join()'

    output_fc       = '{}\{}_joined'.format(output_FGDB, os.path.basename(target_fc))
    join_operation   = 'JOIN_ONE_TO_MANY'

    print '  Spatially Joining:\n    {}\n  With:\n    {}\n  Joined FC at:\n    {}'.format(target_fc, join_fc, output_fc)
    arcpy.SpatialJoin_analysis(target_fc, join_fc, output_fc, join_operation)

    print 'Finished Join_2_FC_By_Spatial_Join()\n'

    return output_fc

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                    FUNCTION Join 2 Objects by Attribute

def Join_2_Objects_By_Attr(target_obj, target_join_field, to_join_obj, to_join_field, join_type):
    """
    PARAMETERS:
      target_obj (str): The full path to the FC or Table that you want to have
        another object join to.

      target_join_field (str): The field name in the target_obj to be used as the
        primary key.

      to_join_obj (str): The full path to the FC or Table that you want to join
        to the target_obj.

      to_join_field (str): The field name in the to_join_obj to be used as the
        foreign key.

      join_type (str): Specifies what will be done with records in the input
        that match a record in the join table. Valid values:
          KEEP_ALL
          KEEP_COMMON

    RETURNS:
      target_obj (lyr): Return the layer/view of the joined object so that
        it can be processed.

    FUNCTION:
      To join two different objects via a primary key field and a foreign key
      field by:
        1) Creating a layer or table view for each object ('target_obj', 'to_join_obj')
        2) Joining the layer(s) / view(s) via the 'target_join_field' and the
           'to_join_field'

    NOTE:
      This function returns a layer/view of the joined object, remember to delete
      the joined object (arcpy.Delete_management(target_obj)) if performing
      multiple joins in one script.
    """

    print '\n    Starting Join_2_Objects_By_Attr()...'

    # Create the layer or view for the target_obj using try/except
    try:
        arcpy.MakeFeatureLayer_management(target_obj, 'target_obj')
        print '      Made FEATURE LAYER for: {}'.format(target_obj)
    except:
        arcpy.MakeTableView_management(target_obj, 'target_obj')
        print '      Made TABLE VIEW for: {}'.format(target_obj)

    # Create the layer or view for the to_join_obj using try/except
    try:
        arcpy.MakeFeatureLayer_management(to_join_obj, 'to_join_obj')
        print '      Made FEATURE LAYER for: {}'.format(to_join_obj)
    except:
        arcpy.MakeTableView_management(to_join_obj, 'to_join_obj')
        print '      Made TABLE VIEW for: {}'.format(to_join_obj)

    # Join the layers
    print '      Joining "{}"\n         With "{}"\n           On "{}"\n         Type "{}"\n'.format(target_obj, to_join_obj, to_join_field, join_type)
    arcpy.AddJoin_management('target_obj', target_join_field, 'to_join_obj', to_join_field, join_type)

    # Print the fields (only really needed during testing)
    ##fields = arcpy.ListFields('target_obj')
    ##print '  Fields in joined layer:'
    ##for field in fields:
    ##    print '    ' + field.name

    print '    Finished Join_2_Objects_By_Attr()\n'

    # Return the layer/view of the joined object so it can be processed
    return 'target_obj'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                    FUNCTION: New Loc and Loc Desc
def New_Loc_LocDesc(wkg_data, DPW_WP_SITES):
    """
    NOTE: This function is from DPW_Science_and_Monitoring.py, but is no longer
    being used in that script.

    PARAMETERS:

    RETURNS:

    FUNCTION:
    """

    print '--------------------------------------------------------------------'
    print 'Getting new Location Descriptions and Locations from:\n  {}\n'.format(wkg_data)

    #---------------------------------------------------------------------------
    #                      Get new Location Descriptions.

    # Create list and add the first item
    New_LocDescs = ['  The following are New Location Description suggested changes (Please edit associated feature class appropriately):']

    # Create a Search cursor and add data to lists
    cursor_fields = ['SampleEventID', 'Creator', 'StationID', 'site_loc_desc_new']
    where = "site_loc_desc_cor = 'No'"
    with arcpy.da.SearchCursor(wkg_data, cursor_fields, where) as cursor:

        for row in cursor:
            New_LocDesc = ('    For SampleEventID: "{}", Monitor: "{}" said the Location Description for StationID: "{}" was innacurate.  Suggested change: "{}"\n'.format(row[0], row[1], row[2], row[3]))
            New_LocDescs.append(New_LocDesc)

    del cursor

    # If there is only the original New_LocDescs string, then there were no new
    # suggested changes to make, replace the original string with below
    if (len(New_LocDescs) == 1):
        New_LocDescs = ['  There were no New Location Description suggested changes.\n']

    for desc in New_LocDescs:
        print desc

    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                           Set new Locations

    # Create needed lists
    New_Locs = ['  The following are the sites that were relocated in the field (The changes will be automatically made to the DPW_WP_SITES):']
    StationIDs, ShapeXs, ShapeYs, SampEvntIDs, Creators = ([] for i in range(5))

    # Create Search cursor and add data to lists
    cursor_fields = ['StationID', 'Shape@X', 'Shape@Y', 'SampleEventID', 'Creator']
    where = "site_loc_map_cor = 'No'"
    with arcpy.da.SearchCursor(wkg_data, cursor_fields, where) as cursor:

        for row in cursor:
            StationID    = row[0]
            ShapeX       = row[1]
            ShapeY       = row[2]
            SampleEvntID = row[3]
            Creator      = row[4]

            StationIDs.append(StationID)
            ShapeXs.append(ShapeX)
            ShapeYs.append(ShapeY)
            SampEvntIDs.append(SampleEvntID)
            Creators.append(Creator)

            ##print 'StationID: "{}" has an NEW X of: "{}" and a NEW Y of: "{}"'.format(StationID, ShapeX, ShapeY)

            New_Loc = ('    For SampleEventID: "{}", Monitor: "{}" said the Location Description for StationID: "{}" was innacurate.  Site has been moved.\n'.format(SampleEvntID, Creator, StationID))
            New_Locs.append(New_Loc)

    del cursor

   # If there is only the original New_Locs string, then there were no new
   #  locations to move; no need to update the DPW_WP_SITES
    if(len(New_Locs) == 1):
        New_Locs = ['  There were no relocated sites.\n']

    #---------------------------------------------------------------------------
    # Create an Update cursor to update the Shape column in the DPW_WP_SITES
    else:
        list_counter = 0
        cursor_fields = ['StationID', 'Shape@X', 'Shape@Y']
        with arcpy.da.UpdateCursor(DPW_WP_SITES, cursor_fields) as cursor:
            for row in cursor:

                # Only loop as many times as there are StationIDs to update
                if (list_counter < len(StationIDs)):

                    # If StationID in DPW_WP_SITES equals the StationID in the
                    #  StationIDs list, update the geom for that StationID in DPW_WP_SITES
                    if row[0] == StationIDs[list_counter]:
                        ##print '  Updating StationID: {} with new coordinates.'.format(StationIDs[list_counter])

                        # Give Shape@X and Shape@Y their new values
                        row[1] = ShapeXs[list_counter]
                        row[2] = ShapeYs[list_counter]

                        cursor.updateRow(row)

                        list_counter += 1

        del cursor

        #-----------------------------------------------------------------------
        # Calculate X and Y fields in DPW_WP_SITES now that the geometry has been updated

        # Calculate the Long_X field
        field = 'Long_X'
        expression = "!Shape.Centroid.X!"
        expression_type="PYTHON_9.3"
        arcpy.CalculateField_management(DPW_WP_SITES, field, expression, expression_type)

        # Calculate the Lat_Y field now that the geometry has been updated
        field = 'Lat_Y'
        expression = "!Shape.Centroid.Y!"
        expression_type="PYTHON_9.3"
        arcpy.CalculateField_management(DPW_WP_SITES, field, expression, expression_type)

    for Loc in New_Locs:
        print Loc


    print '\nSuccessfully got new Location Descriptions and set New Locations.\n'

    return New_LocDescs, New_Locs

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION Select_Object()
def Select_By_Attribute(path_to_obj, selection_type, where_clause):
    """
    PARAMETERS:
      path_to_obj (str): Full path to the object (Feature Class or Table) that
        is to be selected.

      selection_type (str): Selection type.  Valid values are:
        NEW_SELECTION
        ADD_TO_SELECTION
        REMOVE_FROM_SELECTION
        SUBSET_SELECTION
        SWITCH_SELECTION
        CLEAR_SELECTION

      where_clause (str): The SQL where clause.

    RETURNS:
      'lyr' (lyr): The layer/view with the selection on it.

    FUNCTION:
      To perform a selection on the object.
    """

    print 'Starting Select_Object()...'

    # Use try/except to handle either object type (Feature Layer / Table)
    try:
        arcpy.MakeFeatureLayer_management(path_to_obj, 'lyr')
    except:
        arcpy.MakeTableView_management(path_to_obj, 'lyr')

    print '  Selecting "lyr" with a selection type: {}, where: "{}"'.format(selection_type, where_clause)
    arcpy.SelectLayerByAttribute_management('lyr', selection_type, where_clause)

    print 'Finished Select_Object()\n'
    return 'lyr'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#            FUNCTION: Set Date the AGOL data was Downloaded
def Set_Date_Data_DL(fc_w_timestamp, fc_to_update):
    """
    PARAMETERS:
      fc_w_timestamp (str): Full path to a FC that contains a time stamp
        of when the data was downloaded (or was 'current').  The time stamp
        should be in the format 'YYYY_MM_DD__HH_MM_SS'.
        i.e. 'Data_From_AGOL_2018_01_01__10_00_00'

      fc_to_update (str): Full path to a FC or Table that contains a field named
        'AGOL_Data_Last_Downloaded'.  This is the field that we will write the
        read-friendly formatted time stamp.  If the field name is different,
        that name will have to be specified below in the function itself.

        i.e. a time stamp of:
          2018_01_01__14_00_00
        will become:
          01 Jan, 2018 - 02:00:00 PM

    RETURNS:
      None

    FUNCTION:
      To turn a FC or Table time stamp from 'YYYY_MM_DD__HH_MM_SS' to
      'DD Month, YYYY - HH:MM:SS AM/PM' and set that read-friendly string into
      another FC or Table.
      Specifically we are setting the date and time the data
      was downloaded from AGOL into a FC that will be used to report when the
      data was downloaded.
    """
    print '--------------------------------------------------------------------'
    print 'Starting Set_Date_Data_DL()'

    import time

    # Get the last 20 characters from the FC name (i.e. "2018_02_02__11_11_33")
    dt_stripped = fc_w_timestamp[-20:]

    # Parse the string to time and format the time
    t = time.strptime(dt_stripped, '%Y_%m_%d__%H_%M_%S')
    t_formatted = time.mktime(t)

    # Format time back into a string (i.e. "02 Feb, 2018 - 11:11:33 AM"
    AGOL_data_downloaded = time.strftime("%d %b, %Y - %I:%M:%S %p", time.localtime(t_formatted))

    # Field Calculate the string into the fc_to_update FC
    fc = fc_to_update
    field = 'AGOL_Data_Last_Downloaded'
    expression = '"{}"'.format(AGOL_data_downloaded)

    print '  Calculating field:\n    {}\n  In fc:\n    {} '.format(field, fc)
    print '  To equal:\n    {}'.format(expression)

    arcpy.CalculateField_management(fc, field, expression)

    print 'Finished Set_Date_Data_DL()\n'

    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Test_Exists(dataset):
    """
    PARAMETERS:
      dataset (str): Full path to a dataset.  May be a FC, Table, etc.

    RETURNS:
      exists (bool): 'True' if the dataset exists, 'False' if not.

    FUNCTION:
      To test if a dataset exists or not.
    """

    print 'Starting Test_Exists()'

    print '  Testing to see if exists: "{}"'.format(dataset)

    # Test to see if 'dataset' exists or not
    if arcpy.Exists(dataset):
        exists = True
    else:
        exists = False

    print '  Dataset Exists = "{}"'.format(exists)

    print 'Finished Test_Exists\n'

    return exists

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Test_Schema_Lock()
def Test_Schema_Lock(dataset):
    """
    PARAMETERS:
      dataset (str): Full path to a dataset to be tested if there is a schema lock

    RETURNS:
      no_schema_lock (Boolean): "True" or "False" if there is no schema lock

    FUNCTION:
      To perform a test on a dataset and return "True" if there is no schema
      lock, and "False" if a schema lock already exists.
    """

    print 'Starting Test_Schema_Lock()...'

    print '  Testing dataset: {}'.format(dataset)

    no_schema_lock = arcpy.TestSchemaLock(dataset)
    print '  Dataset available to have a schema lock applied to it = "{}"'.format(no_schema_lock)

    print 'Finished Test_Schema_Lock()\n'

    return no_schema_lock

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         FUNCTION Update_Cursor_Func()
def Update_Cursor_Func(fc_or_table, field_to_update, id_field, where_clause, value):
    """
    PARAMETERS:
      fc_or_table (str): Full path to a Feature Class or Table to be updated.

      field_to_update (str): Name of the field to be updated.

      id_field (str): Name of the field that acts as a record identifier for the
        user.  Not crucial for the function to run, but useful for the user to
        see which record(s) modified by this function.

      where_clause (str): A SQL string used to return only records that satisfy
        this clause.  Examples that can be directly copied and pasted:
          '"LAYER_NAME" = \'ECO_MSCP_CN_NORTH_DRAFT\''
          '"LAYER_NAME" like \'HYD%\''

      value (str/obj/num): Can be a string (if going into a text field)
                               or a datetime object (if going into a date field)
                               or a number (if going into a numerical field)

    RETURNS:
      None

    FUNCTION:
      To update a 'field_to_update' in a 'fc_or_table' with the 'value' supplied
      using a 'where_clause' to refine the rows that will be updated.

    NOTE:
      This function uses the older arcpy.UpdateCursor() function.  While this
      method works without having to start an edit session if updating an SDE
      (unlike the arcpy.da.UpdateCursor which requires an edit session), the
      arcpy.UpdateCursor is slower and older.
      It is at risk to be discontinued at some point in the future.

    CREATED:
      8/8/2017--Mike Grue
    EDITED:
      8/8/2017--Mike Grue
    """

    import arcpy
    print 'Starting Update_Cursor_Func()'

    # Print statements with all the variables
    print '  Updating fc or table  "{}"'.format(fc_or_table)
    print '    Field being updated "{}"'.format(field_to_update)
    print '                  where  {}'.format(where_clause)
    print '             with value "{}"\n'.format(value)

    #---------------------------------------------------------------------------
    try:
        cursor = arcpy.UpdateCursor(fc_or_table, where_clause)
        row = cursor.next()
        while row:
            print '\n----------------------------------------------------------'
            # Get and print the current value
            id_to_print = row.getValue(id_field)
            current_val = row.getValue(field_to_update)
            print '  Current value for "{}" in field "{}" is "{}"'.format(id_to_print, field_to_update, current_val)

            # Set the value and print the new value
            row.setValue(field_to_update, value)
            print '  New value "{}"'.format(row.getValue(field_to_update))

            # Update and move to next row (if there is one)
            cursor.updateRow(row)
            row = cursor.next()

        del cursor  # Delete the cursor in order for the updates to 'save'
    except Exception as e:
        print '*** ERROR with UpdateCursor() ***'
        print str(e)

    print '\nFinished Update_Cursor_Func()'

    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         FUNCTION: Update_Fields()

def Update_Fields(target_obj, join_field, obj_to_join, fields_to_update):
    """
    PARAMETERS:
      target_obj (str): The full path of the FC/Table to be updated.

      join_field (str): The name of the field used to join the two objects.

      obj_to_join (str): The full path of the FC/Table used to update.

      fields_to_update (list): List of the field names that will be updated.
        Field names must match between the target_obj and the obj_to_join

    RETURNS:
      none

    FUNCTION:
      To calculate the fields in 'fields_to_update' list from the obj_to_join
      to the target_obj

    NOTE:
      This Function needs access to Join_2_Objects() function in order to work.
    """

    print 'Starting Update_Fields()...'

    joined_obj = Join_2_Objects(target_obj, join_field, obj_to_join, join_field, 'KEEP_COMMON')

    # Get the basename of the imported table, i.e. "CIP_5YEAR_POLY_2017_5_15__9_38_50"
    # Will be used in 'expression' below
    obj_to_join_name = os.path.basename(obj_to_join)

    # Get the basename of the target_obj i.e. 'CIP_5YEAR_POLY'
    # Will be used in the 'where_clause' and 'SearchCursor' below
    target_obj_name = os.path.basename(target_obj)

    for field in fields_to_update:

        field_to_calc = '{}.{}'.format(target_obj_name, field)
        expression    = '!{}.{}!'.format(obj_to_join_name, field)

        print '  In joined_fc, calculating field: "{}", to equal: "{}"'.format(field_to_calc, expression)
        arcpy.CalculateField_management(joined_obj, field_to_calc, expression, 'PYTHON_9.3')

    # Delete the layer/view between the SDW FC and the imported table so there
    #   is no 'holdover' when creating the next joined layer/view
    print '\n  Deleting layer/view with the join'
    arcpy.Delete_management(joined_obj)

    print 'Finished Updating Fields\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Write_Print_To_Log()
def Write_Print_To_Log(log_file):
    """
    PARAMETERS:
      log_file (str): Path to log file.  The part after the last "\" will be the
        name of the .log file after the date, time, and ".log" is appended to it.

    RETURNS:
      orig_stdout (os object): The original stdout is saved in this variable so
        that the script can access it and return stdout back to its orig settings.

    FUNCTION:
      To turn all the 'print' statements into a log-writing object.  A new log
        file will be created based on log_file with the date, time, ".log"
        appended to it.  And any print statements after the command
        "sys.stdout = write_to_log" will be written to this log.
      It is a good idea to use the returned orig_stdout variable to return sys.stdout
        back to its original setting.
      NOTE: This function needs the function Get_DT_To_Append() to run

    """
    print 'Starting Write_Print_To_Log()...'

    # Get the original sys.stdout so it can be returned to normal at the
    #    end of the script.
    orig_stdout = sys.stdout

    # Get DateTime to append
    dt_to_append = Get_DT_To_Append()

    # Create the log file with the datetime appended to the file name
    log_file_date = '{}_{}.log'.format(log_file,dt_to_append)
    write_to_log = open(log_file_date, 'w')

    # Make the 'print' statement write to the log file
    print '  Setting "print" command to write to a log file found at:\n  {}'.format(log_file_date)
    sys.stdout = write_to_log

    # Header for log file
    start_time = datetime.datetime.now()
    start_time_str = [start_time.strftime('%m/%d/%Y  %I:%M:%S %p')][0]
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    print '                  {}'.format(start_time_str)
    print '             START <name_of_script_here>.py'
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n'

    return orig_stdout

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------