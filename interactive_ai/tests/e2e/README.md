**TODO: CVS-160717 move this information to the internal documentation**

# e2e BDD tests

## Setup

### Install requirements

1. Install nvm https://github.com/nvm-sh/nvm
2. Make sure you use nvm 16 `nvm install 16` then `nvm use 16`
3. Install swagger CLI: `npm install -g @apidevtools/swagger-cli`
4. Install OpenAPI Generator CLI: `npm install @openapitools/openapi-generator-cli -g` (requires Java 11 or higher `sudo apt install default-jre` then `java -version`)

### Obtain a Personal Access Token

In the UI, go to the 'Account' section, select the 'Token' tab and click on 'Create' to generate an access token.

### Setup the environment

Set the following environment variables:

- `GETI_SERVER_URL` -> address of the Geti server
- `GETI_API_KEY` -> your personal access token

The S3 credentials are required to download the test data; if you already have the data cached locally, you can skip setting these variables.
If you don't know the credentials, ask the team.

## Run the tests

To run all the tests: `make tests`

To only run smoke tests: `make test_smoke`

To only run tests tagged `@wip`: `make test_wip`

To run tests for a specific feature (e.g. `label_addition`): `make tests FEATURE=label_addition`

To run tests for a specific feature and a specific tag (e.g. `@smoke`): `make tests BDD_TAG=@smoke FEATURE=label_addition`
(or equivalently `make test_smoke FEATURE=label_addition`)

To run tests with a complex [tag expression](https://behave.readthedocs.io/en/latest/tag_expressions/): `uv run behave --tags=<tag_expression>`

For more details about the usage of behave, check its [official documentation](https://behave.readthedocs.io/en/latest/).

## Generate reports

`make tests` will generate a JUnit report for each feature in the `bdd/reports` folder.
You can convert these reports to HTML with `make report` and open them in your browser.
