// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { path } from 'static-path';

const root = path('/');

const organization = root.path('/organizations/:organizationId');
const workspace = organization.path('/workspaces/:workspaceId');
const home = workspace;
const project = workspace.path('/projects/:projectId');
const dataset = project.path('/datasets/:datasetId');
const models = project.path('/models');
const model = models.path('/:groupId/:modelId');
const modelVariants = model.path('/model-variants');
const requestedAccess = root.path('/requested-access');

const tests = project.path('tests');

const register = root.path('registration');
const account = organization.path('/account');
const users = account.path('/users');

const annotator = dataset.path('/annotator');

const intelAdmin = process.env.REACT_APP_BUILD_TARGET === 'admin_standalone' ? root : root.path('/intel-admin');

const restApiSpecs = root.path('/rest-api/openapi-specification');

export const paths = {
    root,
    home,
    requestedAccess,
    restApiSpecs,
    organization: {
        index: organization,
        about: organization.path('/about'),
    },

    docs: path('/docs/'),
    authProviderCallback: path('/callback'),
    logout: path('/logout'),
    account: {
        index: account,
        profile: account.path('/profile'),
        personalAccessToken: account.path('/personal-access-token'),
        security: account.path('/security'),
        analytics: account.path('/analytics'),
        storage: account.path('/storage'),
        usage: account.path('/usage'),
        users: {
            index: users,
            details: users.path('/details'),
        },
        workspaces: account.path('/workspaces'),
    },
    workspace,
    users: workspace.path('/users'),
    project: {
        index: project,
        labels: project.path('/labels'),
        template: project.path('/template'),
        dataset: {
            index: dataset,
            media: dataset.path('/media'),
            statistics: dataset.path('/statistics'),
            camera: dataset.path('/camera'),
            capturedMediaGallery: dataset.path('/camera/gallery/'),
        },
        models: {
            index: models,
            model: {
                index: model,
                modelVariants: {
                    index: modelVariants,
                    onnx: modelVariants.path('/onnx'),
                    pytorch: modelVariants.path('/pytorch'),
                    openVino: modelVariants.path('/openvino'),
                },
                datasets: model.path('/training-datasets'),
                statistics: model.path('/statistics'),
                parameters: model.path('/parameters'),
                labels: model.path('/labels'),
            },
        },
        tests: {
            index: tests,
            livePrediction: tests.path('/live-prediction'),
            test: tests.path('/:testId'),
        },
        deployments: project.path('/deployments'),
        users: project.path('/users'),

        annotator: {
            index: annotator,
            image: annotator.path('/image/:imageId'),
            video: annotator.path('/video/:videoId'),
            videoFrame: annotator.path('/video/:videoId/:frameNumber'),
        },
    },

    register: {
        index: register,
        signUp: register.path('sign-up'),
        forgotPassword: register.path('forgot-password'),
        resetPassword: register.path('reset-password'),
        invalidLink: register.path('invalid-link'),
        userNotFound: register.path('/users/not-found'),
    },

    intelAdmin: {
        index: intelAdmin,
        organizations: intelAdmin.path('/organizations'),
        organization: {
            index: intelAdmin.path('/organizations/:organizationId'),
            overview: intelAdmin.path('/organizations/:organizationId/overview'),
            creditAccounts: intelAdmin.path('/organizations/:organizationId/credits'),
            serviceLimits: intelAdmin.path('/organizations/:organizationId/limits'),
            coupons: intelAdmin.path('/organizations/:organizationId/coupons'),
            users: intelAdmin.path('/organizations/:organizationId/users'),
        },
        authProviderCallback: intelAdmin.path('/callback'),
        logout: intelAdmin.path('/logout'),
        users: intelAdmin.path('/users'),
        user: {
            index: intelAdmin.path('/users/:userId'),
            overview: intelAdmin.path('/users/:userId/overview'),
            memberships: intelAdmin.path('/users/:userId/memberships'),
        },
    },

    signOut: path('/oauth2/sign_out'),
    signOutPage: path('/sign_out_page'),
};
