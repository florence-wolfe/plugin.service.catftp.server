# Kodi FTP Server Add-on

The Kodi FTP Server add-on allows you to run an FTP server directly from your Kodi media center. It provides a convenient way to access your Kodi files locally using an FTP client.

The FTP Server implementation is a minmally forked version of [pyftpdlib@1.5.9](https://pypi.org/project/pyftpdlib/1.5.9/) for Kodi.

## ⚠️ **Important Security Notice** ⚠️
This add-on is intended for local use only and should not be exposed to the public internet. Running an FTP server can pose security risks if not properly configured and secured. Use this add-on at your own risk and ensure that it is only accessible within your local network. The add-on author and contributors shall not be held liable for any damages or issues arising from the misuse or improper configuration of this add-on.

## Features

- Run an FTP server directly from Kodi
- Access Kodi files locally using an FTP client
- Configurable port and credentials
- Easy setup and configuration through the Kodi add-on settings
- Automatically starts the FTP server when launching Kodi

Future planned work is to allow users to enable SFTP and provide their own certificates.

## Configuration

1. Open the Kodi FTP Server add-on settings by navigating to "Add-ons" > "Services" > "Kodi FTP Server" and selecting "Configure".

2. Configure the following settings according to your preferences:
   - FTP Port: The port number on which the FTP server will listen (default: 2121).
   - FTP Username: The username required to access the FTP server (default: "kodi").
   - FTP Password: The password required to access the FTP server (default: "kodi").

3. Ensure that the configured port is not accessible from outside your local network.

4. **Note:** Modifying the server settings will require restarting Kodi for the changes to take effect as the FTP server initializes when you start Kodi and there is no settings change listener coded yet.

## Usage

1. The Kodi FTP Server add-on automatically starts the FTP server when launching Kodi.

2. The FTP server will run on the configured port using the specified username and password.

3. Use an FTP client (e.g., FileZilla) to connect to the Kodi FTP server using the local IP address of your Kodi device, the configured port, username, and password.

4. Once connected, you can browse, upload, and download files from your Kodi media center.

5. To stop the FTP server, you need to exit Kodi.

Future work will allow both starting and stopping the server with a script.

## Troubleshooting

- If you encounter any issues or errors, please enable debugging in the Kodi FTP Server add-on settings and check the Kodi log file for detailed information.
- Make sure the configured port is not being used by any other application or service on your local network.
- Ensure that your FTP client is configured to connect to the correct local IP address and port.
- If you modify the server settings, remember to restart Kodi for the changes to take effect.

## Contributing

Contributions to the Kodi FTP Server add-on are welcome! If you find any bugs, have feature requests, or want to contribute improvements, please open an issue or submit a pull request on the [GitHub repository](https://github.com/yourusername/kodi-ftp-server).

## License

This add-on is licensed under the [MIT License](LICENSE).

## Disclaimer

The Kodi FTP Server add-on is provided as-is, without any warranty or guarantee of its functionality or security. Use it at your own risk and only within your local network. The add-on author and contributors shall not be held liable for any damages or issues arising from the use or misuse of this add-on.