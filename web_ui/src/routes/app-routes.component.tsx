// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Suspense, useEffect } from 'react';

import { IntelBrandedLoading } from '@geti/ui';
import { negate } from 'lodash-es';
import { Navigate, Outlet, Route, useLocation } from 'react-router-dom';

import { AnalyticsProvider } from '../analytics/analytics-provider.component';
import { useFeatureFlags } from '../core/feature-flags/hooks/use-feature-flags.hook';
import { isKeypointTask } from '../core/projects/utils';
import { useEventListener } from '../hooks/event-listener/event-listener.hook';
import { useIsSaasEnv } from '../hooks/use-is-saas-env/use-is-saas-env.hook';
import { useStorage } from '../hooks/use-storage/use-storage';
import { Notifications, useNotification } from '../notification/notification.component';
import { TaskProvider } from '../pages/annotator/providers/task-provider/task-provider.component';
import { RouterErrorBoundary } from '../pages/errors/router-error-boundary.component';
import { WelcomeTrialModal } from '../pages/landing-page/welcome-trial-modal/welcome-trial-modal.component';
import { ProjectDataset } from '../pages/project-details/components/project-dataset/project-dataset.component';
import { RequestAccessConfirmation } from '../pages/sign-up/request-access-confirmation.component';
import { SignUp } from '../pages/sign-up/sign-up.component';
import { TusUploadProvider } from '../providers/tus-upload-provider/tus-upload-provider.component';
import { AccessDeniedDialog } from '../shared/components/access-denied-dialog/access-denied-dialog.component';
import { LicenseModal } from '../shared/components/license-modal/license-modal.component';
import { ForgotPassword } from '../sign-up/pages/forgot-password/forgot-password.component';
import { InvalidLink } from '../sign-up/pages/invalid-link/invalid-link.component';
import { Registration } from '../sign-up/pages/registration/registration.component';
import { ResetPassword } from '../sign-up/pages/reset-password/reset-password.component';
import { UserNotFound } from '../sign-up/pages/user-not-found/user-not-found.component';
import { paths } from '@geti/core/src/services/routes';
import { MediaUploadProvider } from './../providers/media-upload-provider/media-upload-provider.component';
import { ProjectsImportProvider } from './../providers/projects-import-provider/projects-import-provider.component';
import { AboutRoute } from './about.route';
import { AuthenticationLayout } from './auth/auth.layout';
import { LogoutRoute } from './auth/logout.route';
import { CameraScreenRoute } from './camera.route';
import { MediaGalleryRoute } from './captured-media-gallery.route';
import { IndexRoute } from './index.route';
import { LandingPageLayout } from './landing-page.layout';
import { LastLoginNotification } from './last-login-notification/last-login-notification';
import { OrganizationsContext } from './organizations/organizations-context.component';
import { UserManagementRoute } from './profile/index.route';
import { AnnotatorRoute } from './projects/annotator.route';
import { DatasetRoute } from './projects/dataset.route';
import { DeploymentsRoute } from './projects/deployments.route';
import { LabelsRoute } from './projects/labels.route';
import { ProjectLayout } from './projects/layout';
import { ModelsRoute } from './projects/models/index.route';
import { ModelRoute } from './projects/models/model.route';
import { ProjectProviderLayout } from './projects/project-provider.layout';
import { TemplateRoute } from './projects/template.route';
import { TestsRoute } from './projects/tests/index.route';
import { TestRoute } from './projects/tests/test.route';
import { ProjectUsersRoute } from './projects/users';
import {
    CallbackRedirect,
    RedirectIfSaaS,
    RedirectIfTaskIs,
    RedirectToDatasetMedia,
    RedirectToOpenVino,
    RedirectToOptimizedModel,
    RedirectToUsersProfile,
    RedirectToWorkspace,
} from './redirect.component';
import { RoutesCollector } from './routes-collector.component';
import { UsersRoute } from './users/index.route';

// Lazy loading in react router 6.4:
// https://dev.to/infoxicator/data-routers-code-splitting-23no
// https://www.robinwieruch.de/react-router-lazy-loading/
// https://github.com/remix-run/react-router/discussions/9393

const ErrorsHandler = (): JSX.Element => {
    const { isOpenDialogAccessDenied, handleClose } = useStorage();

    return <AccessDeniedDialog isOpen={isOpenDialogAccessDenied} handleClose={handleClose} />;
};

const AppProviders = (): JSX.Element => {
    const isSaaS = useIsSaasEnv();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();

    const location = useLocation();
    const { removeNotifications } = useNotification();

    useEffect(() => {
        removeNotifications();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [location]);

    useEventListener('error', (e) => {
        // Virtuoso's resize observer can throw this error, which is caught by DnD's
        // global window.error listener and aborts dragging.
        // To prevent this from happening we need to register an error listener before
        // DnD's listener that prevents the event from propagating
        if (
            e.message === 'ResizeObserver loop completed with undelivered notifications.' ||
            e.message === 'ResizeObserver loop limit exceeded'
        ) {
            e.stopImmediatePropagation();
        }
    });

    return (
        <Suspense fallback={<IntelBrandedLoading />}>
            <AnalyticsProvider>
                <RoutesCollector>
                    <OrganizationsContext>
                        <LastLoginNotification />
                        <TusUploadProvider>
                            <MediaUploadProvider>
                                <ProjectsImportProvider>
                                    <Outlet />
                                    {FEATURE_FLAG_CREDIT_SYSTEM && isSaaS && <WelcomeTrialModal />}
                                    {!isSaaS && <LicenseModal />}
                                </ProjectsImportProvider>
                            </MediaUploadProvider>
                        </TusUploadProvider>
                    </OrganizationsContext>
                </RoutesCollector>
            </AnalyticsProvider>
            <ErrorsHandler />
        </Suspense>
    );
};

export const appRoutes = () => {
    return (
        <Route
            element={
                <>
                    <Notifications />
                    <Outlet />
                </>
            }
            errorElement={<RouterErrorBoundary />}
        >
            <Route path={paths.logout.pattern} element={<LogoutRoute home={paths.root({})} />} />
            <Route
                path={paths.restApiSpecs.pattern}
                lazy={async () => {
                    const { RestApiSpecs } = await import('./rest-api-specs/rest-api-specs');

                    return { Component: RestApiSpecs };
                }}
            />

            <Route
                path={paths.register.index.pattern}
                element={
                    <RedirectIfSaaS>
                        <Outlet />
                    </RedirectIfSaaS>
                }
            >
                <Route path={paths.register.signUp.pattern} element={<Registration />} />
                <Route path={paths.register.forgotPassword.pattern} element={<ForgotPassword />} />
                <Route path={paths.register.resetPassword.pattern} element={<ResetPassword />} />
                <Route path={paths.register.invalidLink.pattern} element={<InvalidLink />} />
                <Route path={paths.register.userNotFound.pattern} element={<UserNotFound />} />
                <Route path={'*'} element={<Navigate to={paths.register.signUp({})} replace />} />
            </Route>

            <Route element={<AuthenticationLayout />}>
                <Route path={paths.requestedAccess.pattern} element={<RequestAccessConfirmation />} />

                {/* route requires workspace */}
                <Route
                    path={paths.root.pattern}
                    element={
                        <SignUp>
                            <AppProviders />
                        </SignUp>
                    }
                >
                    {/* OIDC callback route */}
                    <Route path={paths.authProviderCallback.pattern} element={<CallbackRedirect />} />

                    {/* Redirect to a route with user's workspace */}
                    <Route index element={<RedirectToWorkspace />} />
                    <Route path={paths.organization.index.pattern} element={<RedirectToWorkspace />} />

                    {/* Landing page */}
                    <Route path={paths.root.pattern} element={<LandingPageLayout />}>
                        <Route path={paths.workspace.pattern} element={<IndexRoute />} />
                        <Route path={paths.account.index.pattern}>
                            <Route element={<RedirectToUsersProfile />} index />
                            <Route path={paths.account.profile.pattern} element={<UserManagementRoute />} />
                            <Route path={paths.account.personalAccessToken.pattern} element={<UserManagementRoute />} />
                            <Route path={paths.account.security.pattern} element={<UserManagementRoute />} />
                            <Route path={paths.account.analytics.pattern} element={<UserManagementRoute />} />
                            <Route path={paths.account.workspaces.pattern} element={<UserManagementRoute />} />
                            <Route path={paths.account.storage.pattern} element={<UserManagementRoute />} />
                            <Route path={paths.account.usage.pattern} element={<UserManagementRoute />} />
                            <Route path={paths.account.users.index.pattern} element={<UserManagementRoute />} />
                        </Route>

                        <Route path={paths.organization.about.pattern} element={<AboutRoute />} />
                        <Route path={paths.users.pattern} element={<UsersRoute />} />
                    </Route>

                    {/* Project page */}
                    <Route
                        path={paths.project.index.pattern}
                        element={
                            <Suspense fallback={<IntelBrandedLoading />}>
                                <ProjectProviderLayout />
                            </Suspense>
                        }
                    >
                        {/** camera page */}
                        <Route
                            path={paths.project.dataset.camera.pattern}
                            element={
                                <TaskProvider>
                                    <CameraScreenRoute />
                                </TaskProvider>
                            }
                        />

                        {/** captured media gallery page */}
                        <Route
                            path={paths.project.dataset.capturedMediaGallery.pattern}
                            element={
                                <TaskProvider>
                                    <MediaGalleryRoute />
                                </TaskProvider>
                            }
                        />
                        <Route path={paths.project.index.pattern} element={<ProjectLayout />}>
                            <Route index element={<RedirectToDatasetMedia />} />
                            <Route
                                path={paths.project.labels.pattern}
                                element={
                                    <RedirectIfTaskIs predicate={isKeypointTask} to={'template'}>
                                        <LabelsRoute />
                                    </RedirectIfTaskIs>
                                }
                            />
                            <Route
                                path={paths.project.template.pattern}
                                element={
                                    <RedirectIfTaskIs predicate={negate(isKeypointTask)} to={'labels'}>
                                        <TemplateRoute />
                                    </RedirectIfTaskIs>
                                }
                            />

                            <Route path={paths.project.dataset.index.pattern} element={<DatasetRoute />}>
                                <Route index element={<RedirectToDatasetMedia />} />

                                {/* TODO split ProjectDatasetScreen into different routes */}
                                <Route path={paths.project.dataset.statistics.pattern} element={<ProjectDataset />} />
                                <Route path={paths.project.dataset.media.pattern} element={<ProjectDataset />} />
                            </Route>

                            <Route path={paths.project.models.index.pattern}>
                                <Route element={<ModelsRoute />} index />

                                <Route path={paths.project.models.model.index.pattern}>
                                    <Route index element={<RedirectToOptimizedModel />} />

                                    <Route path={paths.project.models.model.modelVariants.index.pattern}>
                                        <Route index element={<RedirectToOpenVino />} />

                                        <Route
                                            path={paths.project.models.model.modelVariants.onnx.pattern}
                                            element={<ModelRoute />}
                                        />
                                        <Route
                                            path={paths.project.models.model.modelVariants.openVino.pattern}
                                            element={<ModelRoute />}
                                        />
                                        <Route
                                            path={paths.project.models.model.modelVariants.pytorch.pattern}
                                            element={<ModelRoute />}
                                        />
                                    </Route>

                                    <Route
                                        path={paths.project.models.model.datasets.pattern}
                                        element={<ModelRoute />}
                                    />
                                    <Route
                                        path={paths.project.models.model.parameters.pattern}
                                        element={<ModelRoute />}
                                    />
                                    <Route
                                        path={paths.project.models.model.statistics.pattern}
                                        element={<ModelRoute />}
                                    />
                                    <Route path={paths.project.models.model.labels.pattern} element={<ModelRoute />} />
                                </Route>
                            </Route>

                            <Route path={paths.project.tests.index.pattern}>
                                <Route element={<TestsRoute />} index />
                                <Route path={paths.project.tests.livePrediction.pattern} element={<TestsRoute />} />
                                <Route path={paths.project.tests.test.pattern} element={<TestRoute />} />
                            </Route>

                            <Route path={paths.project.deployments.pattern} element={<DeploymentsRoute />} />

                            <Route path={paths.project.users.pattern} element={<ProjectUsersRoute />} />
                        </Route>

                        {/* We don't want to use the Project dataset screen's layout */}
                        <Route path={paths.project.annotator.index.pattern} element={<AnnotatorRoute />}>
                            <Route path={paths.project.annotator.image.pattern} element={<AnnotatorRoute />} />
                            <Route path={paths.project.annotator.video.pattern} element={<AnnotatorRoute />} />
                            <Route path={paths.project.annotator.videoFrame.pattern} element={<AnnotatorRoute />} />
                        </Route>
                    </Route>
                </Route>
                <Route path={'*'} element={<Navigate to={paths.root({})} replace />} />
            </Route>
        </Route>
    );
};
