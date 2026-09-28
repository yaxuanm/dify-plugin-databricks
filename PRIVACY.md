# Privacy Policy for Databricks SQL

Last updated: September 28, 2026

## Scope

This policy applies to the Databricks SQL Dify plugin.

## Data processed

To perform a tool invocation, the plugin processes the Databricks workspace host, authentication token, warehouse ID, catalog, schema, SQL statement, job ID, run ID, and the response returned by the configured Databricks workspace.

## Data use and sharing

The plugin sends invocation data only to the Databricks workspace configured by the user. It does not send data to developer-controlled services or other third parties.

## Storage and retention

The plugin does not write credentials or query results to developer-controlled storage. Data retention for the Dify deployment and Databricks workspace is governed by their respective configurations and policies.

## Security

Use HTTPS for the configured workspace host. Credentials are supplied to the plugin through Dify's credential configuration and are used only to authenticate requests to the configured Databricks workspace. The plugin does not log authentication token values.

## Contact

For privacy questions or to report an issue, open an issue in the [source repository](https://github.com/yaxuanm/dify-plugin-databricks/issues).
