"""From: https://github.com/dougbrion/OctoRest"""

import os
from contextlib import contextmanager
from urllib import parse as urlparse
from typing import Optional, Tuple
from enum import Enum
from time import sleep

import requests


class AuthorizationRequestPollingResult(Enum):
    STILL_WAITING = 1
    GRANTED = 2
    NOPE = 3  # Request denied or request timed out by the server


class WorkflowAppKeyRequestResult(Enum):
    WORKFLOW_UNSUPPORTED = 1
    NOPE = 2  # Request denied or request timed out by the server
    GRANTED = 3
    TIMED_OUT = 4


class OctoRest:
    """
    Encapsulates communication with one OctoPrint instance
    """

    def __init__(self, *, url=None, apikey=None, session=None):
        """
        Initialize the object with URL and API key

        If a session is provided, it will be used (mostly for testing)
        """
        if not url:
            raise TypeError("Required argument 'url' not found or empty")

        parsed = urlparse.urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            raise TypeError("Provided URL is not HTTP(S)")
        if not parsed.netloc:
            raise TypeError("Provided URL is empty")

        self.url = "{}://{}".format(parsed.scheme, parsed.netloc)

        self.session = session or requests.Session()

        if apikey:
            self.load_api_key(apikey)

    def load_api_key(self, apikey: str) -> None:
        """Use the given API key for all future communication with the OctoPrint server.

        Raises TypeError if 'apikey' is None or empty.
        Raises RuntimeError if the API key is rejected by the server.

        """
        if not apikey:
            raise TypeError("Required argument 'apikey' not found or empty")

        self.session.headers.update({"X-Api-Key": apikey})

        # Try a simple request to see if the API key works
        # Keep the info, in case we need it later
        self.version = self.get_version()

    def _get(self, path, params=None):
        """
        Perform HTTP GET on given path with the auth header

        Path shall be the ending part of the URL,
        i.e. it should not be full URL

        Raises a RuntimeError when not 20x OK-ish

        Returns JSON decoded data
        """
        url = urlparse.urljoin(self.url, path)
        response = self.session.get(url, params=params)
        self._check_response(response)

        return response.json()

    def _post(self, path, data=None, files=None, json=None, ret=True):
        """
        Perform HTTP POST on given path with the auth header

        Path shall be the ending part of the URL,
        i.e. it should not be full URL

        Raises a RuntimeError when not 20x OK-ish

        Returns JSON decoded data
        """
        url = urlparse.urljoin(self.url, path)
        response = self.session.post(url, data=data, files=files, json=json)
        self._check_response(response)

        if ret:
            return response.json()

    def _delete(self, path):
        """
        Perform HTTP DELETE on given path with the auth header

        Path shall be the ending part of the URL,
        i.e. it should not be full URL

        Raises a RuntimeError when not 20x OK-ish

        Returns nothing
        """
        url = urlparse.urljoin(self.url, path)
        response = self.session.delete(url)
        self._check_response(response)

    def _put(self, path, data=None, files=None, json=None, ret=True):
        """
        Perform HTTP PUT on given path with the auth header

        Path shall be the ending part of the URL,
        i.e. it should not be full URL

        Raises a RuntimeError when not 20x OK-ish

        Returns JSON decoded data
        """
        url = urlparse.urljoin(self.url, path)
        response = self.session.put(url, data=data, files=files, json=json)
        self._check_response(response)

        if ret:
            return response.json()

    def _patch(self, path, data=None, files=None, json=None, ret=True):
        """
        Perform HTTP PATCH on given path with the auth header

        Path shall be the ending part of the URL,
        i.e. it should not be full URL

        Raises a RuntimeError when not 20x OK-ish

        Returns JSON decoded data
        """
        url = urlparse.urljoin(self.url, path)
        response = self.session.patch(url, data=data, files=files, json=json)
        self._check_response(response)

        if ret:
            return response.json()

    def _check_response(self, response):
        """
        Make sure the response status code was 20x, raise otherwise
        """
        if not (200 <= response.status_code < 210):
            error = response.text
            msg = "Reply for {} was not OK: {} ({})"
            msg = msg.format(response.url, error, response.status_code)
            raise RuntimeError(msg)
        return response

    ###########################
    ### VERSION INFORMATION ###
    ###########################

    def _version_tuple(self, v):
        return tuple(map(int, (v.split("."))))

    def get_version(self):
        """Version information
        http://docs.octoprint.org/en/master/api/version.html#version-information

        Retrieve information regarding server and API version
        """
        return self._get("/api/version")

    ##############
    ### LOGIN  ###
    ##############

    def current_user(self):
        """Current User
        https://docs.octoprint.org/en/master/api/general.html#current-user

        Retrieves information about the current user.
        """
        return self._get("/api/currentuser")

    ###########################
    ### APPS - SESSION KEYS ###
    ###########################

    def tmp_session_key(self):
        """Obtaining a temporary session key
        http://docs.octoprint.org/en/master/api/apps.html#obtaining-a-temporary-session-key

        Retrieve a temporary session key with a minimum validity.
        It can only be used as a proper API key after having been verified.
        Returns the temporary session key and the timestamp until it’s valid.

        Deprecated since version 1.3.11: This functionality will be removed in 1.4.0.
        Use the Application Keys Plugin workflow instead.
        """
        return self._get("/apps/auth")

    def verify_tmp_session_key(self):
        """Verifying a temporary session key
        http://docs.octoprint.org/en/master/api/apps.html#verifying-a-temporary-session-key

        Verify a formerly retrieved temporary session key by providing
        credentials and a cryptographic signature over these credentials
        and the temporary key.
        Returns the now verified session key and the new validity.

        Deprecated since version 1.3.11: This functionality will be removed in 1.4.0.
        Use the Application Keys Plugin workflow instead.
        """
        return self._post("/apps/auth")

    ###############################################
    ### APPS - APPLICATION KEYS PLUGIN WORKFLOW ###
    ###############################################

    def probe_app_keys_workflow_support(self) -> bool:
        """Check if the Application Keys Plugin workflow is supported
        https://docs.octoprint.org/en/master/bundledplugins/appkeys.html#probe-for-workflow-support

        Raises ConnectionError if the OctoPrint server could not be found.

        Returns True if the workflow is supported, otherwise returns False.
        """
        url = urlparse.urljoin(self.url, "/plugin/appkeys/probe")
        response = self.session.get(url)

        if response.status_code == 204:
            return True

        return False

    def start_authorization_process(self, app: str, user: Optional[str] = None) -> str:
        """Starts the authorization process
        https://docs.octoprint.org/en/master/bundledplugins/appkeys.html#start-authorization-process

        app: This parameter should be a human readable identifier to use for the application requesting access.
        It will be displayed to the user.
        Internally it will be used case insensitively, so `My App` and `my APP` are considered the same application identifiers.

        user: The optional `user` parameter should be used to limit the authorization process to a specified user.
        If the parameter is left unset, any user will be able to complete the authorization process and
        grant access to the app with their account. E.g. if a user `me` starts the process in an app,
        the app should request that name from the user and use it in the `user` parameter.
        OctoPrint will then only display the authorization request on browsers the user `me` is logged in on.

        Raises a RuntimeError when the server response does not indicate that the authorization process started.

        Returns the polling URL.
        """
        data = {"app": app}

        if user:
            data["user"] = user

        url = urlparse.urljoin(self.url, "/plugin/appkeys/request")
        response = self.session.post(url, json=data)
        self._check_response(response)

        location = response.headers["Location"]

        return location

    def poll_auth_request_decision(
        self, url: str
    ) -> Tuple[AuthorizationRequestPollingResult, Optional[str]]:
        """Check for an authorization request decision
        https://docs.octoprint.org/en/master/bundledplugins/appkeys.html#poll-for-decision-on-existing-request

        url: The polling url received from OctoRest.startAuthorizationProcess()

        Returns a tuple who's first item an enum representing the result type,
        and if the result type is GRANTED, the tuple's second item is the API key.
        """

        response = self.session.get(url)

        if response.status_code == 202:
            return (AuthorizationRequestPollingResult.STILL_WAITING, None)
        elif response.status_code == 404:
            return (AuthorizationRequestPollingResult.NOPE, None)
        elif response.status_code == 200:
            key_response = response.json()
            api_key = key_response[
                "api_key"
            ]  # At the time of writing this, the official documentation in the link above says this key is named 'apikey', but wireshark says differently
            return (AuthorizationRequestPollingResult.GRANTED, api_key)
        else:
            raise Exception("Received response with unexpected status code")

    def try_get_api_key(
        self, appName: str, user: Optional[str], timeout: int = 60
    ) -> Tuple[WorkflowAppKeyRequestResult, Optional[str]]:
        """Run the Application Keys Plugin Workflow

        app: This parameter should be a human readable identifier to use for the application requesting access.
        It will be displayed to the user.
        Internally it will be used case insensitively, so `My App` and `my APP` are considered the same application identifiers.

        user: The optional `user` parameter should be used to limit the authorization process to a specified user.
        If the parameter is left unset, any user will be able to complete the authorization process and
        grant access to the app with their account. E.g. if a user `me` starts the process in an app,
        the app should request that name from the user and use it in the `user` parameter.
        OctoPrint will then only display the authorization request on browsers the user `me` is logged in on.

        timeout: the amount of time (in seconds) to wait for the user to approve the key request.

        Raises ConnectionError if the OctoPrint server could not be found.

        Returns a tuple who's first item an enum representing the result type,
        and if the result type is GRANTED, the tuple's second item is the API key.
        """
        workflow_supported = self.probe_app_keys_workflow_support()

        if not workflow_supported:
            return (WorkflowAppKeyRequestResult.WORKFLOW_UNSUPPORTED, None)

        polling_url = self.start_authorization_process(appName, user)

        interval = 1
        elapsed = 0

        while elapsed < timeout:
            (polling_result, api_key) = self.poll_auth_request_decision(polling_url)

            if polling_result == AuthorizationRequestPollingResult.NOPE:
                return (WorkflowAppKeyRequestResult.NOPE, None)

            if polling_result == AuthorizationRequestPollingResult.GRANTED:
                return (WorkflowAppKeyRequestResult.GRANTED, api_key)

            sleep(interval)
            elapsed += interval

        return (WorkflowAppKeyRequestResult.TIMED_OUT, None)

    ###########################
    ### CONNECTION HANDLING ###
    ###########################

    def connection_info(self):
        """Get connection settings
        http://docs.octoprint.org/en/master/api/connection.html#get-connection-settings

        Retrieve the current connection settings, including information
        regarding the available baudrates and serial ports and the
        current connection state.
        """
        return self._get("/api/connection")

    def state(self):
        """
        A shortcut to get the current state.
        """
        return self.connection_info()["current"]["state"]

    def connect(
        self,
        *,
        port=None,
        baudrate=None,
        printer_profile=None,
        save=None,
        autoconnect=None
    ):
        """Issue a connection command
        http://docs.octoprint.org/en/master/api/connection.html#issue-a-connection-command

        Instructs OctoPrint to connect to the printer

        port: Optional, specific port to connect to. If not set the current
        portPreference will be used, or if no preference is available auto
        detection will be attempted.

        baudrate: Optional, specific baudrate to connect with. If not set
        the current baudratePreference will be used, or if no preference
        is available auto detection will be attempted.

        printer_profile: Optional, specific printer profile to use for
        connection. If not set the current default printer profile
        will be used.

        save: Optional, whether to save the request's port and baudrate
        settings as new preferences. Defaults to false if not set.

        autoconnect: Optional, whether to automatically connect to the printer
        on OctoPrint's startup in the future. If not set no changes will be
        made to the current configuration.
        """
        data = {"command": "connect"}
        if port is not None:
            data["port"] = port
        if baudrate is not None:
            data["baudrate"] = baudrate
        if printer_profile is not None:
            data["printerProfile"] = printer_profile
        if save is not None:
            data["save"] = save
        if autoconnect is not None:
            data["autoconnect"] = autoconnect
        self._post("/api/connection", json=data, ret=False)

    def disconnect(self):
        """Issue a connection command
        http://docs.octoprint.org/en/master/api/connection.html#issue-a-connection-command

        Instructs OctoPrint to disconnect from the printer
        """
        data = {"command": "disconnect"}
        self._post("/api/connection", json=data, ret=False)

    def fake_ack(self):
        """Issue a connection command
        http://docs.octoprint.org/en/master/api/connection.html#issue-a-connection-command

        Fakes an acknowledgment message for OctoPrint in case one got lost on
        the serial line and the communication with the printer since stalled.
        This should only be used in "emergencies" (e.g. to save prints), the
        reason for the lost acknowledgment should always be properly
        investigated and removed instead of depending on this "symptom solver".
        """
        data = {"command": "fake_ack"}
        self._post("/api/connection", json=data, ret=False)

    #######################
    ### FILE OPERATIONS ###
    #######################

    def _prepend_local(self, location):
        if location.split("/")[0] not in ("local", "sdcard"):
            return "local/" + location
        return location

    def files(self, location=None, recursive=False):
        """Retrieve all files
        http://docs.octoprint.org/en/master/api/files.html#retrieve-all-files

        Retrieve files from specific location
        http://docs.octoprint.org/en/master/api/files.html#retrieve-files-from-specific-location

        Retrieve information regarding all files currently available and
        regarding the disk space still available locally in the system

        If location is used, retrieve information regarding the files currently
        available on the selected location and - if targeting the local
        location - regarding the disk space still available locally in the
        system

        If location is a file, retrieves the selected file''s information

        Args:
            location: The origin location from which to retrieve the files.
                      Currently only local and sdcard are supported, with local
                      referring to files stored in OctoPrint’s uploads folder
                      and sdcard referring to files stored on the printer’s
                      SD card (if available).
            recursive: If set to true, return all files and folders recursively.
                       Otherwise only return items on same level.

        TODO: Recursive appears to always be on
        """
        payload = {"recursive": str(recursive).lower()}
        if location:
            location = self._prepend_local(location)
            return self._get("/api/files/{}".format(location), params=payload)
        return self._get("/api/files", params=payload)

    @contextmanager
    def _file_tuple(self, file):
        """
        Yields a tuple with filename and file object

        Expects the same thing or a path as input
        """
        mime = "application/octet-stream"

        try:
            exists = os.path.exists(file)
        except:
            exists = False

        if exists:
            filename = os.path.basename(file)
            with open(file, "rb") as f:
                yield (filename, f, mime)
        else:
            yield file + (mime,)

    def files_info(self, location, filename, recursive=False):
        """Retrieve a specific file’s or folder’s information
        http://docs.octoprint.org/en/master/api/files.html#retrieve-a-specific-file-s-or-folder-s-information

        Retrieves the selected file’s or folder’s information.
        If the file is unknown, a 404 Not Found is returned.
        If the targeted path is a folder, by default only its direct children
        will be returned. If recursive is provided and set to true, all
        sub folders and their children will be returned too.
        On success, a 200 OK is returned, with a file information item as
        the response body.
        """
        payload = {"recursive": str(recursive).lower()}
        return self._get("/api/files/{}/{}".format(location, filename), params=payload)

    def upload(
        self,
        file,
        *,
        location="local",
        select=False,
        print=False,
        userdata=None,
        path=None
    ):
        """Upload file or create folder
        http://docs.octoprint.org/en/master/api/files.html#upload-file-or-create-folder

        Upload a given file
        It can be a path or a tuple with a filename and a file-like object
        """
        with self._file_tuple(file) as file_tuple:
            files = {
                "file": file_tuple,
                "select": (None, select),
                "print": (None, print),
            }
            if userdata:
                files["userdata"] = (None, userdata)
            if path:
                files["path"] = (None, path)

            return self._post("/api/files/{}".format(location), files=files)

    def new_folder(self, folder_name, location="local"):
        """Upload file or create folder
        http://docs.octoprint.org/en/master/api/files.html#upload-file-or-create-folder

        To create a new folder, the request body must at least contain the foldername
        form field, specifying the name of the new folder. Note that folder creation
        is currently only supported on the local file system.
        """
        data = {
            "foldername": folder_name,
        }
        return self._post("/api/files/{}".format(location), data=data)

    def select(self, location, *, print=False):
        """Issue a file command
        http://docs.octoprint.org/en/master/api/files.html#issue-a-file-command

        Selects a file for printing

        Location is target/filename, defaults to local/filename
        If print is True, the selected file starts to print immediately
        """
        location = self._prepend_local(location)
        data = {
            "command": "select",
            "print": print,
        }
        self._post("/api/files/{}".format(location), json=data, ret=False)

    def slice(
        self,
        location,
        slicer="curalegacy",
        gcode=None,
        position=None,
        printer_profile=None,
        profile=None,
        select=False,
        print=False,
    ):
        """Issue a file command
        http://docs.octoprint.org/en/master/api/files.html#issue-a-file-command

        Slices an STL file into GCODE.
        Note that this is an asynchronous operation that
        will take place in the background after the response
        has been sent back to the client.

        TODO: ADD PROFILE.*
        """
        location = self._prepend_local(location)
        data = {
            "command": "slice",
            "slicer": slicer,
            "select": select,
            "print": print,
        }
        if gcode is not None:
            data["gcode"] = gcode
        if position is not None:
            data["position"] = position
        if printer_profile is not None:
            data["printerProfile"] = printer_profile
        if profile is not None:
            data["profile"] = profile
        return self._post("/api/files/{}".format(location), json=data, ret=False)

    def copy(self, location, dest):
        """Issue a file command
        http://docs.octoprint.org/en/master/api/files.html#issue-a-file-command

        Copies the file or folder to a new destination on the same location
        """
        location = self._prepend_local(location)
        data = {
            "command": "copy",
            "destination": dest,
        }
        return self._post("/api/files/{}".format(location), json=data, ret=False)

    def move(self, location, dest):
        """Issue a file command
        http://docs.octoprint.org/en/master/api/files.html#issue-a-file-command

        Moves the file or folder to a new destination on the same location
        """
        location = self._prepend_local(location)
        data = {
            "command": "move",
            "destination": dest,
        }
        return self._post("/api/files/{}".format(location), json=data, ret=False)

    def delete(self, location):
        """Delete file
        http://docs.octoprint.org/en/master/api/files.html#delete-file

        Delete the selected filename on the selected target

        Location is target/filename, defaults to local/filename
        """
        location = self._prepend_local(location)
        self._delete("/api/files/{}".format(location))

    ######################
    ### JOB OPERATIONS ###
    ######################

    def start(self):
        """Issue a job command
        http://docs.octoprint.org/en/master/api/job.html#issue-a-job-command

        Starts the print of the currently selected file

        Use select() to select a file
        """
        data = {"command": "start"}
        self._post("/api/job", json=data, ret=False)

    def cancel(self):
        """Issue a job command
        http://docs.octoprint.org/en/master/api/job.html#issue-a-job-command

        Cancels the current print job

        There must be an active print job for this to work
        """
        data = {"command": "cancel"}
        self._post("/api/job", json=data, ret=False)

    def restart(self):
        """Issue a job command
        http://docs.octoprint.org/en/master/api/job.html#issue-a-job-command

        Restart the print of the currently selected file from the beginning

        There must be an active print job for this to work and the print job
        must currently be paused
        """
        data = {"command": "restart"}
        self._post("/api/job", json=data, ret=False)

    def pause_command(self, action):
        """Issue a job command
        http://docs.octoprint.org/en/master/api/job.html#issue-a-job-command

        Pauses/resumes/toggles the current print job.
        Accepts one optional additional parameter action specifying
        which action to take.

        In order to stay backwards compatible to earlier iterations of this API,
        the default action to take if no action parameter is supplied is to
        toggle the print job status.

        Pause:
            Pauses the current job if it’s printing,
            does nothing if it’s already paused.
        Resume:
            Resumes the current job if it’s paused,
            does nothing if it’s printing.
        Toggle:
            Toggles the pause state of the job,
            pausing it if it’s printing and resuming it
            if it’s currently paused.
        """
        data = {
            "command": "pause",
            "action": action,
        }
        self._post("/api/job", json=data, ret=False)

    def pause(self):
        """Issue a job command
        http://docs.octoprint.org/en/master/api/job.html#issue-a-job-command

        Pauses the current job if it’s printing,
        does nothing if it’s already paused.
        """
        self.pause_command(action="pause")

    def resume(self):
        """Issue a job command
        http://docs.octoprint.org/en/master/api/job.html#issue-a-job-command

        Resumes the current job if it’s paused,
        does nothing if it’s printing.
        """
        self.pause_command(action="resume")

    def toggle(self):
        """Issue a job command
        http://docs.octoprint.org/en/master/api/job.html#issue-a-job-command

        Toggles the pause state of the job,
        pausing it if it’s printing and resuming it
        if it’s currently paused.
        """
        self.pause_command(action="toggle")

    def job_info(self):
        """Retrieve information about the current job
        http://docs.octoprint.org/en/master/api/job.html#retrieve-information-about-the-current-job

        Retrieve information about the current job (if there is one)
        """
        return self._get("/api/job")

    #################
    ### LANGUAGES ###
    #################

    def languages(self):
        """Retrieve installed language packs
        http://docs.octoprint.org/en/master/api/languages.html#retrieve-installed-language-packs

        Retrieves a list of installed language packs.
        """
        return self._get("/api/languages")

    def upload_language(self, file):
        """Upload a language pack
        http://docs.octoprint.org/en/master/api/languages.html#upload-a-language-pack

        Uploads a new language pack to OctoPrint.
        Other than most of the other requests on OctoPrint’s API which are
        expected as JSON, this request is expected as
        Content-Type: multipart/form-data due to the included file upload.
        To upload a file, the request body must contain the file form field
        with the contents and file name of the file to upload.
        Only files with one of the extensions zip, tar.gz, tgz or tar will
        be processed, for other file extensions a 400 Bad Request will be returned.
        Will return a list of installed language packs upon completion,
        as described in Retrieve installed language packs.

        Parameters:
            file – The language pack file to upload
        """
        with self._file_tuple(file) as file_tuple:
            files = {"file": file_tuple}

            return self._post("/api/languages", files=files)

    def delete_language(self, locale, pack):
        """Delete a language pack
        http://docs.octoprint.org/en/master/api/languages.html#delete-a-language-pack

        Retrieves a list of installed language packs.
        """
        return self._delete("/api/languages/{}/{}".format(locale, pack))

    ###########################
    ### LOG FILE MANAGEMENT ###
    ###########################

    def logs(self):
        """Retrieve a list of available log files
        http://docs.octoprint.org/en/master/bundledplugins/logging.html#retrieve-a-list-of-available-log-files

        Log file management (and logging configuration) was moved into
        a bundled plugin in OctoPrint 1.3.7.

        Retrieve information regarding all log files currently available
        and regarding the disk space still available in the system on the
        location the log files are being stored
        """
        version = self._version_tuple(self.version["server"])
        if version < self._version_tuple("1.3.7"):
            return self._get("/api/logs")
        return self._get("/plugin/logging/logs")

    def delete_log(self, filename):
        """Delete a specific logfile
        http://docs.octoprint.org/en/master/bundledplugins/logging.html#delete-a-specific-logfile

        Log file management (and logging configuration) was moved into
        a bundled plugin in OctoPrint 1.3.7.

        Delete the selected log file with name filename
        """
        version = self._version_tuple(self.version["server"])
        if version < self._version_tuple("1.3.7"):
            self._delete("/api/logs/{}".format(filename))
        self._delete("/plugin/logging/logs/{}".format(filename))

    ##########################
    ### PRINTER OPERATIONS ###
    ##########################

    def _hwinfo(self, url, **kwargs):
        """
        Helper method for printer(), tool(), bed() and sd()
        """
        params = {}
        if kwargs.get("exclude"):
            params["exclude"] = ",".join(kwargs["exclude"])
        if kwargs.get("history"):
            params["history"] = "true"  # or 'yes' or 'y' or '1'
        if kwargs.get("limit"):
            params["limit"] = kwargs["limit"]
        return self._get(url, params=params)

    def printer(self, *, exclude=None, history=False, limit=None):
        """Retrieve the current printer state
        http://docs.octoprint.org/en/master/api/printer.html#retrieve-the-current-printer-state

        Retrieves the current state of the printer

        Returned information includes:

        * temperature information
        * SD state (if available)
        * general printer state

        Temperature information can also be made to include the printer's
        temperature history by setting the history argument.
        The amount of data points to return here can be limited using the limit
        argument.

        Clients can specify a list of attributes to not return in the response
        (e.g. if they don't need it) via the exclude argument.
        """
        return self._hwinfo(
            "/api/printer", exclude=exclude, history=history, limit=limit
        )

    def jog(self, x=None, y=None, z=None):
        """Issue a print head command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-print-head-command

        Jogs the print head (relatively) by a defined amount in one or more
        axes. Additional parameters are:

        x: Optional. Amount to jog print head on x axis, must be a valid
        number corresponding to the distance to travel in mm.

        y: Optional. Amount to jog print head on y axis, must be a valid
        number corresponding to the distance to travel in mm.

        z: Optional. Amount to jog print head on z axis, must be a valid
        number corresponding to the distance to travel in mm.
        """
        data = {"command": "jog"}
        if x:
            data["x"] = x
        if y:
            data["y"] = y
        if z:
            data["z"] = z
        self._post("/api/printer/printhead", json=data, ret=False)

    def home(self, axes=None):
        """Issue a print head command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-print-head-command

        Homes the print head in all of the given axes.
        Additional parameters are:

        axes: A list of axes which to home, valid values are one or more of
        'x', 'y', 'z'. Defaults to all.
        """
        axes = [a.lower()[:1] for a in axes] if axes else ["x", "y", "z"]
        data = {"command": "home", "axes": axes}
        self._post("/api/printer/printhead", json=data, ret=False)

    def feedrate(self, factor):
        """Issue a print head command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-print-head-command

        Changes the feedrate factor to apply to the movement's of the axes.

        factor: The new factor, percentage as integer or float (percentage
        divided by 100) between 50 and 200%.
        """
        data = {"command": "feedrate", "factor": factor}
        self._post("/api/printer/printhead", json=data, ret=False)

    @classmethod
    def _tool_dict(cls, whatever):
        if isinstance(whatever, (int, float)):
            whatever = (whatever,)
        if isinstance(whatever, dict):
            ret = whatever
        else:
            ret = {}
            for n, thing in enumerate(whatever):
                ret["tool{}".format(n)] = thing
        return ret

    def tool_target(self, targets):
        """Issue a tool command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-tool-command

        Sets the given target temperature on the printer's tools.
        Additional parameters:

        targets: Target temperature(s) to set.
        Can be one number (for tool0), list of numbers or dict, where keys
        must match the format tool{n} with n being the tool's index starting
        with 0.
        """
        targets = self._tool_dict(targets)
        data = {"command": "target", "targets": targets}
        self._post("/api/printer/tool", json=data, ret=False)

    def tool_offset(self, offsets):
        """Issue a tool command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-tool-command

        Sets the given temperature offset on the printer's tools.
        Additional parameters:

        offsets: Offset(s) to set.
        Can be one number (for tool0), list of numbers or dict, where keys
        must match the format tool{n} with n being the tool's index starting
        with 0.
        """
        offsets = self._tool_dict(offsets)
        data = {"command": "offset", "offsets": offsets}
        self._post("/api/printer/tool", json=data, ret=False)

    def tool_select(self, tool):
        """Issue a tool command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-tool-command

        Selects the printer's current tool.
        Additional parameters:

        tool: Tool to select, format tool{n} with n being the tool's index
        starting with 0. Or integer.
        """
        if isinstance(tool, int):
            tool = "tool{}".format(tool)
        data = {"command": "select", "tool": tool}
        self._post("/api/printer/tool", json=data, ret=False)

    def extrude(self, amount):
        """Issue a tool command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-tool-command

        Extrudes the given amount of filament from the currently selected tool

        Additional parameters:

        amount: The amount of filament to extrude in mm.
        May be negative to retract.
        """
        data = {"command": "extrude", "amount": amount}
        self._post("/api/printer/tool", json=data, ret=False)

    def retract(self, amount):
        """Issue a tool command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-tool-command

        Retracts the given amount of filament from the currently selected tool

        Additional parameters:

        amount: The amount of filament to retract in mm.
        May be negative to extrude.
        """
        self.extrude(-amount)

    def flowrate(self, factor):
        """Issue a tool command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-tool-command

        Changes the flow rate factor to apply to extrusion of the tool.

        factor: The new factor, percentage as integer or float
        (percentage divided by 100) between 75 and 125%.
        """
        data = {"command": "flowrate", "factor": factor}
        self._post("/api/printer/tool", json=data, ret=False)

    def tool(self, history=False, limit=None):
        """Retrieve the current tool state
        http://docs.octoprint.org/en/master/api/printer.html#retrieve-the-current-tool-state

        Retrieves the current temperature data (actual, target and offset) plus
        optionally a (limited) history (actual, target, timestamp) for all of
        the printer's available tools.

        It's also possible to retrieve the temperature history by setting the
        history argument. The amount of returned history data points can be
        limited using the limit argument.
        """
        return self._hwinfo("/api/printer/tool", history=history, limit=limit)

    def bed_target(self, target):
        """Issue a bed command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-bed-command

        Sets the given target temperature on the printer's bed.

        target: Target temperature to set.
        """
        data = {"command": "target", "target": target}
        self._post("/api/printer/bed", json=data, ret=False)

    def bed_offset(self, offset):
        """Issue a bed command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-bed-command

        Sets the given temperature offset on the printer's bed.

        offset: Temperature offset to set.
        """
        data = {"command": "offset", "offset": offset}
        self._post("/api/printer/bed", json=data, ret=False)

    def bed(self, history=False, limit=None):
        """Retrieve the current bed state
        http://docs.octoprint.org/en/master/api/printer.html#retrieve-the-current-bed-state

        Retrieves the current temperature data (actual, target and offset) plus
        optionally a (limited) history (actual, target, timestamp) for the
        printer's heated bed.

        It's also possible to retrieve the temperature history by setting the
        history argument. The amount of returned history data points can be
        limited using the limit argument.
        """
        return self._hwinfo("/api/printer/bed", history=history, limit=limit)

    def chamber_target(self, target):
        """Issue a chamber command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-chamber-command

        Sets the given target temperature on the printer's chamber.

        target: Target temperature to set.
        """
        data = {"command": "target", "target": target}
        self._post("/api/printer/chamber", json=data, ret=False)

    def chamber_offset(self, offset):
        """Issue a chamber command
        http://docs.octoprint.org/en/master/api/printer.html#issue-a-chamber-command

        Sets the given temperature offset on the printer's chamber.

        offset: Temperature offset to set.
        """
        data = {"command": "offset", "offset": offset}
        self._post("/api/printer/chamber", json=data, ret=False)

    def chamber(self, history=False, limit=None):
        """Retrieve the current chamber state
        http://docs.octoprint.org/en/master/api/printer.html#retrieve-the-current-chamber-state

        Retrieves the current temperature data (actual, target and offset) plus
        optionally a (limited) history (actual, target, timestamp) for the
        printer's heated chamber.

        It's also possible to retrieve the temperature history by setting the
        history argument. The amount of returned history data points can be
        limited using the limit argument.
        """
        return self._hwinfo("/api/printer/chamber", history=history, limit=limit)

    def sd_init(self):
        """Issue an SD command
        http://docs.octoprint.org/en/master/api/printer.html#issue-an-sd-command

        Initializes the printer's SD card, making it available for use.
        This also includes an initial retrieval of the list of files currently
        stored on the SD card, so after issuing files(location=sd) a retrieval
        of the files on SD card will return a successful result.

        If OctoPrint detects the availability of a SD card on the printer
        during connection, it will automatically attempt to initialize it.
        """
        data = {"command": "init"}
        self._post("/api/printer/sd", json=data, ret=False)

    def sd_refresh(self):
        """Issue an SD command
        http://docs.octoprint.org/en/master/api/printer.html#issue-an-sd-command

        Refreshes the list of files stored on the printer''s SD card.
        Will raise a 409 Conflict if the card has not been initialized yet
        with sd_init().
        """
        data = {"command": "refresh"}
        self._post("/api/printer/sd", json=data, ret=False)

    def sd_release(self):
        """Issue an SD command
        http://docs.octoprint.org/en/master/api/printer.html#issue-an-sd-command

        Releases the SD card from the printer. The reverse operation to init.
        After issuing this command, the SD card won't be available anymore,
        hence and operations targeting files stored on it will fail.
        Will raise a 409 Conflict if the card has not been initialized yet
        with sd_init().
        """
        data = {"command": "release"}
        self._post("/api/printer/sd", json=data, ret=False)

    def sd(self):
        """Retrieve the current SD state
        http://docs.octoprint.org/en/master/api/printer.html#retrieve-the-current-sd-state

        Retrieves the current state of the printer's SD card.

        If SD support has been disabled in OctoPrint's settings,
        a 404 Not Found is risen.
        """
        return self._get("/api/printer/sd")

    def custom_control_request(self):
        """Retrieves the custom controls as configured in config.yaml.
                http://docs.octoprint.org/en/master/api/printer.html#get--api-printer-command-custom
        .
                The response will contain a list of custom control definitions.
                A 200 OK with a List all response will be returned.
        """
        return self._get("/api/printer/command/custom")

    def gcode(self, command):
        """Send an arbitrary command to the printer
        http://docs.octoprint.org/en/master/api/printer.html#send-an-arbitrary-command-to-the-printer

        Sends any command to the printer via the serial interface.
        Should be used with some care as some commands can interfere with or
        even stop a running print job.

        command: A single string command or command separated by newlines
        or a list of commands
        """
        try:
            n_lines = len(command.splitlines())
            command_lst = command.splitlines()
        except AttributeError:
            # already an iterable
            command_lst = list(command)
            n_lines = len(command_lst)
        command_lst = list(map(lambda it: it.strip(), command_lst))
        if n_lines == 1:
            data = {"command": command_lst[0]}
        else:
            data = {"commands": command_lst}
        self._post("/api/printer/command", json=data, ret=False)

    ##################################
    ### PRINTER PROFILE OPERATIONS ###
    ##################################

    def printer_profiles(self):
        """Retrieve all printer profiles
        http://docs.octoprint.org/en/master/api/printerprofiles.html#retrieve-all-printer-profiles

        Retrieves a list of all configured printer profiles.
        """
        return self._get("/api/printerprofiles")

    def printer_profile(self, profile=None):
        """Retrieve specific printer profile
        https://docs.octoprint.org/en/master/api/printerprofiles.html#retrieve-a-single-printer-profile

        Retrieves a single, existing printer profile.
        """
        # Use default if none given
        if profile is None:
            profile = "_default"
        return self._get("/api/printerprofiles/{}".format(profile))

    def add_printer_profile(self, profile_data):
        """Add a new printer profile
        http://docs.octoprint.org/en/master/api/printerprofiles.html#add-a-new-printer-profile

        TODO: Implement this
        """
        return self._post("/api/printerprofiles", json=profile_data)

    def update_printer_profile(self, profile, profile_data):
        """Update an existing printer profile
        http://docs.octoprint.org/en/master/api/printerprofiles.html#update-an-existing-printer-profile

        TODO: Implement this
        """
        return self._patch("/api/printerprofiles/{}".format(profile), json=profile_data)

    def delete_printer_profile(self, profile):
        """Remove an existing printer profile
        http://docs.octoprint.org/en/master/api/printerprofiles.html#remove-an-existing-printer-profile

        Deletes an existing printer profile by its profile identifier.

        If the profile to be deleted is the currently selected profile,
        a 409 Conflict will be returned.
        """
        return self._delete("/api/printerprofiles/{}".format(profile))

    ################
    ### SETTINGS ###
    ################

    def settings(self, settings=None):
        """Retrieve current settings
        http://docs.octoprint.org/en/master/api/settings.html#retrieve-current-settings

        Save settings
        http://docs.octoprint.org/en/master/api/settings.html#save-settings

        Retrieves the current configuration of printer
        python dict format if argument settings is not given

        Saves provided settings in argument settings (if given)
        and retrieves new settings in python dict format
        Expects a python dict with the settings to change as request body.
        This can be either a full settings tree,
        or only a partial tree containing
        only those fields that should be updated.

        Data model described:
        http://docs.octoprint.org/en/master/api/settings.html#data-model
        http://docs.octoprint.org/en/master/configuration/config_yaml.html#config-yaml
        """
        if settings:
            return self._post("/api/settings", json=settings, ret=True)
        else:
            return self._get("/api/settings")

    def regenerate_apikey(self):
        """Regenerate the system wide API key
        http://docs.octoprint.org/en/master/api/settings.html#regenerate-the-system-wide-api-key
        """
        return self._post("/api/settings/apikey")

    def fetch_templates(self):
        """Fetch template data
        http://docs.octoprint.org/en/master/api/settings.html#fetch-template-data

        This API endpoint is in beta. Things might change.
        """
        return self._get("/api/settings/templates")

    ###############
    ### SLICING ###
    ###############

    def slicers(self):
        """List All Slicers and Slicing Profiles
        http://docs.octoprint.org/en/master/api/slicing.html#list-all-slicers-and-slicing-profiles

        Returns a list of all available slicing profiles for all
        registered slicers in the system.

        Returns a 200 OK response with a Slicer list as the body
        upon successful completion.
        """
        return self._get("/api/slicing")

    def slicer_profiles(self, slicer):
        """List Slicing Profiles of a Specific Slicer
        http://docs.octoprint.org/en/master/api/slicing.html#list-slicing-profiles-of-a-specific-slicer

        Returns a list of all available slicing profiles for
        the requested slicer. Returns a 200 OK response with
        a Profile list as the body upon successful completion.
        """
        return self._get("/api/slicing/{}/profiles".format(slicer))

    def slicer_profile(self, slicer, key):
        """Retrieve Specific Profile
        http://docs.octoprint.org/en/master/api/slicing.html#retrieve-specific-profile

        Retrieves the specified profile from the system.

        Returns a 200 OK response with a full Profile as
        the body upon successful completion.
        """
        return self._get("/api/slicing/{}/profiles/{}".format(slicer, key))

    def add_slicer_profile(self, slicer, key, profile):
        """Add Slicing Profile
        http://docs.octoprint.org/en/master/api/slicing.html#add-slicing-profile

        Adds a new slicing profile for the given slicer to the system.
        If the profile identified by key already exists, it will be overwritten.

        Expects a Profile as body.

        Returns a 201 Created and an abridged Profile in the body
        upon successful completion.

        Requires admin rights.

        TODO: Create a profile body to send
        """
        return self._put(
            "/api/slicing/{}/profiles/{}".format(slicer, key), json=profile
        )

    def delete_slicer_profile(self, slicer, key):
        """Delete Slicing Profile
        http://docs.octoprint.org/en/master/api/slicing.html#delete-slicing-profile

        Delete the slicing profile identified by key for the slicer slicer.
        If the profile doesn’t exist, the request will succeed anyway.

        Requires admin rights.
        """
        return self._delete("/api/slicing/{}/profiles/{}".format(slicer, key))

    ##############
    ### SYSTEM ###
    ##############

    def system_commands(self):
        """List all registered system commands
        http://docs.octoprint.org/en/master/api/system.html#list-all-registered-system-commands

        Retrieves all configured system commands.
        A 200 OK with a List all response will be returned.
        """
        return self._get("/api/system/commands")

    def source_system_commands(self, source):
        """List all registered system commands for a source
        http://docs.octoprint.org/en/master/api/system.html#list-all-registered-system-commands-for-a-source

        Retrieves the configured system commands for the specified source.
        The response will contain a list of command definitions.
        """
        return self._get("/api/system/commands/{}".format(source))

    def execute_system_command(self, source, action):
        """Execute a registered system command
        http://docs.octoprint.org/en/master/api/system.html#execute-a-registered-system-command

        Execute the system command action defined in source.
        Example
        Restart OctoPrint via the core system command restart
        (which is available if the server restart command is configured).

        Parameters:
            source – The source for which to list commands,
            currently either core or custom
            action – The identifier of the command, action from its definition
        """

        return self._post(
            "/api/system/commands/{}/{}".format(source, action), ret=False
        )

    #################
    ### TIMELAPSE ###
    #################

    def timelapses(self, unrendered=None):
        """Retrieve a list of timelapses and the current config
        http://docs.octoprint.org/en/master/api/timelapse.html#retrieve-a-list-of-timelapses-and-the-current-config

        Retrieve a list of timelapses and the current config.
        Returns a timelase list in the response body.

        Unrendered, if True also includes unrendered timelapse.
        """
        if unrendered:
            return self._get("/api/timelapse", params=unrendered)
        return self._get("/api/timelapse")

    def delete_timelapse(self, filename):
        """Delete a timelapse
        http://docs.octoprint.org/en/master/api/timelapse.html#delete-a-timelapse

        Delete the specified timelapse

        Requires user rights
        """
        self._delete("/api/timelapse/{}".format(filename))

    def render_timelapse(self, name):
        """Issue a command for an unrendered timelapse
        http://docs.octoprint.org/en/master/api/timelapse.html#issue-a-command-for-an-unrendered-timelapse

        Current only supports to render the unrendered timelapse
        name via the render command.

        Requires user rights.

        name - The name of the unrendered timelapse
        command – The command to issue, currently only render is supported
        """
        data = {
            "command": "render",
        }
        return self._post("/api/timelapse/unrendered/{}".format(name), json=data)

    def delete_unrendered_timelapse(self, filename):
        """Delete an unrendered timelapse
        http://docs.octoprint.org/en/master/api/timelapse.html#delete-an-unrendered-timelapse
        """
        self._delete("/api/timelapse/unrendered/{}".format(filename))

    def change_timelapse_config(self, type):
        """Change current timelapse config
        http://docs.octoprint.org/en/master/api/timelapse.html#change-current-timelapse-config

        Save a new timelapse configuration to use for the next print.
        The configuration is expected as the request body.
        Requires user rights.

        Type of the timelapse, either off, zchange or timed.

        TODO: setup timelapse configuration
        """
        data = {
            "type": type,
        }
        return self._post("/api/timelapse", json=data)

    ############
    ### USER ###
    ############

    def users(self):
        """Retrieve a list of users
        http://docs.octoprint.org/en/master/api/users.html#retrieve-a-list-of-users

        Retrieves a list of all registered users in OctoPrint.
        Will return a 200 OK with a user list response as body.
        Requires admin rights.
        """
        return self._get("/api/users")

    def user(self, username):
        """Retrieve a user
        http://docs.octoprint.org/en/master/api/users.html#retrieve-a-user

        Retrieves information about a user.
        Will return a 200 OK with a user record as body.
        Requires either admin rights or to be logged in as the user.

        Parameters:
            username – Name of the user which to retrieve
        """
        return self._get("/api/users/{}".format(username))

    def add_user(self, name, password, active=False, admin=False):
        """Add a user
        http://docs.octoprint.org/en/master/api/users.html#add-a-user

        Adds a user to OctoPrint.
        Expects a user registration request as request body.
        Returns a list of registered users on success, see Retrieve a list of users.
        Requires admin rights.

        JSON Params:
            name – The user’s name
            password – The user’s password
            active – Whether to activate the account (true) or not (false)
            admin – Whether to give the account admin rights (true) or not (false)
        """
        data = {
            "name": name,
            "password": password,
            "active": str(active).lower(),
            "admin": str(admin).lower(),
        }
        return self._post("/api/users", json=data)

    def update_user(self, username, admin=None, active=None):
        """Update a user
        http://docs.octoprint.org/en/master/api/users.html#update-a-user

        Updates a user record.
        Expects a user update request as request body.
        Returns a list of registered users on success, see Retrieve a list of users.
        Requires admin rights.

        Parameters:
            username – Name of the user to update

        JSON Params:
            admin – Whether to mark the user as admin (true) or not (false), can be left out (no change)
            active – Whether to mark the account as activated (true) or deactivated (false), can be left out (no change)
        """
        data = {}
        if admin:
            data["admin"] = str(admin).lower()
        if active:
            data["active"] = str(active).lower()
        return self._put("/api/users/{}".format(username), json=data)

    def delete_user(self, username):
        """Delete a user
        http://docs.octoprint.org/en/master/api/users.html#delete-a-user

        Delete a user record.
        Returns a list of registered users on success, see Retrieve a list of users.
        Requires admin rights.

        Parameters:
            username – Name of the user to delete
        """
        return self._delete("/api/users/{}".format(username))

    def reset_user_password(self, username, password):
        """Reset a user’s password
        http://docs.octoprint.org/en/master/api/users.html#reset-a-user-s-password

        Changes the password of a user.
        Expects a JSON object with a single property password as request body.
        Requires admin rights or to be logged in as the user.

        Parameters:
            username – Name of the user to change the password for

        JSON Params:
            password – The new password to set
        """
        data = {
            "password": password,
        }
        return self._put("/api/users/{}/password".format(username), json=data)

    def user_settings(self, username):
        """Retrieve a user’s settings
        http://docs.octoprint.org/en/master/api/users.html#retrieve-a-user-s-settings

        Retrieves a user’s settings.
        Will return a 200 OK with a JSON object representing the user’s
        personal settings (if any) as body.
        Requires admin rights or to be logged in as the user.

        Parameters:
            username - Name of the user to retrieve the settings for
        """
        return self._get("/api/users/{}/settings".format(username))

    def update_user_settings(self, username, new_settings):
        """Update a user’s settings
        http://docs.octoprint.org/en/master/api/users.html#update-a-user-s-settings
        """
        return self._patch("/api/users/{}/settings".format(username), json=new_settings)

    def regenerate_user_apikey(self, username):
        """Regenerate a user’s personal API key
        http://docs.octoprint.org/en/master/api/users.html#regenerate-a-user-s-personal-api-key

        Generates a new API key for the user.
        Does not expect a body. Will return the generated API key as apikey
        property in the JSON object contained in the response body.
        Requires admin rights or to be logged in as the user.

        Parameters:
            username – Name of the user to retrieve the settings for
        """
        return self._post("/api/users/{}/apikey".format(username))

    def delete_user_apikey(self, username):
        """Delete a user’s personal API key
        http://docs.octoprint.org/en/master/api/users.html#delete-a-user-s-personal-api-key

        Deletes a user’s personal API key.
        Requires admin rights or to be logged in as the user.

        Parameters:
            username – Name of the user to retrieve the settings for
        """
        return self._delete("/api/users/{}/apikey".format(username))

    ############
    ### UTIL ###
    ############

    def util_test_path(
        self,
        path,
        check_type,
        check_access,
        allow_create_dir=False,
        check_writable_dir=False,
    ):
        """Test paths or URLs
        http://docs.octoprint.org/en/master/api/util.html#test-paths-or-urls

        check_type: either 'file' or 'dir'
        """
        data = {
            "command": "path",
            "path": path,
            "check_type": check_type,
            "check_access": check_access,
        }
        if check_type == "dir":
            data["allow_create_dir"] = str(allow_create_dir).lower()
            data["check_writable_dir"] = str(check_writable_dir).lower()
        return self._post("/api/util/test", json=data)

    def util_test_url(self, url, status, method, response, timeout=120):
        """Test paths or URLs
        http://docs.octoprint.org/en/master/api/util.html#test-paths-or-urls
        """
        data = {
            "command": "url",
            "url": url,
            "status": status,
            "method": method,
            "response": response,
            "timeout": timeout,
        }
        return self._post("/api/util/test", json=data)

    def util_test_server(self, host, port, protocol, timeout=None):
        """Test paths or URLs
        http://docs.octoprint.org/en/master/api/util.html#test-paths-or-urls
        """
        data = {
            "command": "server",
            "host": host,
            "port": port,
            "protocol": protocol,
        }
        if timeout:
            data["timeout"] = timeout
        return self._post("/api/util/test", json=data)

    ##############
    ### WIZARD ###
    ##############

    def wizard(self):
        """Retrieve additional data about registered wizards
        http://docs.octoprint.org/en/master/api/wizard.html#retrieve-additional-data-about-registered-wizards

        Retrieves additional data about the registered wizards.

        Returns a 200 OK with an object mapping wizard identifiers to wizard
        data entries.
        """
        return self._get("/setup/wizard")

    def finish_wizards(self, handled):
        """Finish wizards
        http://docs.octoprint.org/en/master/api/wizard.html#finish-wizards

        Inform wizards that the wizard dialog has been finished.

        Expects a JSON request body containing a property handled
        which holds a list of wizard identifiers which were handled
        (not skipped) in the wizard dialog.

        Will call octoprint.plugin.WizardPlugin.on_wizard_finish()
        for all registered wizard plugins, supplying the information
        whether the wizard plugin’s identifier was within the list of
        handled wizards or not.
        """
        data = {
            "handled": handled,
        }
        return self._post("/setup/wizard", json=data)
