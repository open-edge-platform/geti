**TODO: CVS-160717 move this information to the internal documentation**

# e2e BDD tests

## Setup

### Install requirements

1. Move to the BDD folder `cd tests/bdd`
2. Install requirements (optionally use a venv): `pip install -r requirements.txt`
3. Install nvm https://github.com/nvm-sh/nvm
4. Make sure you use nvm 16 `nvm install 16` then `nvm use 16`
5. Install swagger CLI: `npm install -g @apidevtools/swagger-cli`
6. Install OpenAPI Generator CLI: `npm install @openapitools/openapi-generator-cli -g` (requires Java 11 or higher `sudo apt install default-jre` then `java -version`)

### Generate the API client for the first time

Generate and install the client with:

1. `make generate_client`
2. `pip install -e rest_client`

If you modify the OpenAPI spec, the client will automatically regenerate (if needed) when you run `make test`.
Alternatively, you can manually rebuild it with `make generate_client_if_needed`.

### Obtain a Personal Access Token

In the UI, go the the 'Account' section, select the 'Token' tab and click on 'Create' to generate an access token.

### Setup the environment

Set the following environment variables:

- `GETI_SERVER_URL` -> address of the Geti server
- `GETI_API_KEY` -> your personal access token
- `AWS_ACCESS_KEY_ID` -> Access key for the [S3 server](https://s3.toolbox.iotg.sclab.intel.com/minio/login)
- `AWS_SECRET_ACCESS_KEY` -> Secret key for the [S3 server](https://s3.toolbox.iotg.sclab.intel.com/minio/login)

The S3 credentials are required to download the test data; if you already have the data cached locally, you can skip setting these variables.
If you don't know the credentials, ask the team.

## Run the tests

To run all the tests: `make test`

To only run smoke tests: `make test_smoke`

To only run tests tagged `@wip`: `make test_wip`

To run tests for a specific feature (e.g. `label_addition`): `make test FEATURE=label_addition`

To run tests for a specific feature and a specific tag (e.g. `@smoke`): `make test BDD_TAG=@smoke FEATURE=label_addition`
(or equivalently `make test_smoke FEATURE=label_addition`)

To run tests with a complex [tag expression](https://behave.readthedocs.io/en/latest/tag_expressions/): `python -m behave --tags=<tag_expression>`

For more details about the usage of behave, check its [official documentation](https://behave.readthedocs.io/en/latest/).

## Generate reports

`make test` will generate a JUnit report for each feature in the `bdd/reports` folder.
You can convert these reports to HTML with `make report` and open them in your browser.
