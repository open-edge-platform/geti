# syntax=docker/dockerfile:1.7

#############
# build_rest_api_specs
#############

FROM node:22.12-bookworm-slim@sha256:35531c52ce27b6575d69755c73e65d4468dba93a25644eed56dc12879cae9213 AS build_rest_api_specs

ARG LOCATION=/home/app/rest-api-specs/

WORKDIR ${LOCATION}

COPY --link ./package.json .
COPY --link --from=docs_context rest_api /home/app/docs/rest_api/
COPY --link --from=api_context schemas /home/app/interactive_ai/services/api/schemas/

RUN npm run build:rest-openapi-spec


#############
# web_ui_deps
#############
FROM node:22.12-bookworm-slim@sha256:35531c52ce27b6575d69755c73e65d4468dba93a25644eed56dc12879cae9213 AS web_ui_deps

ARG LOCATION=/home/app/web_ui/

WORKDIR ${LOCATION}

COPY --link package.json ./
COPY --link package-lock.json ./
COPY --link packages/ packages/
RUN npm ci --audit=false

COPY --link ./eslint.config.js ./
COPY --link ./.prettierrc ./
COPY --link ./tsconfig.json ./
COPY --link ./rsbuild.config.ts ./
COPY --link ./dev-proxy.ts ./

COPY --link src/ src/
COPY --link public/ public/

COPY --from=docs_context rest_api /home/app/docs/rest_api/
COPY --from=api_context schemas /home/app/interactive_ai/services/api/schemas/

RUN npm run build

#######
# web_ui
#######

FROM nginx:1.27-bookworm@sha256:6784fb0834aa7dbbe12e3d7471e69c290df3e6ba810dc38b34ae33d3c1c05f7d AS web_ui

COPY --link --from=web_ui_deps /home/app/web_ui/build/app/ /usr/share/nginx/webui/
COPY --link --from=web_ui_deps /home/app/web_ui/build/admin/ /usr/share/nginx/admin-app/
RUN useradd -u 10001 webservice
COPY --link nginx.conf /etc/nginx/nginx.conf
COPY --link src/maintenance /maintenance
COPY --link --from=build_rest_api_specs /home/app/rest-api-specs/public/openapi-spec.json /usr/share/nginx/webui/openapi-spec.json

USER webservice
EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
