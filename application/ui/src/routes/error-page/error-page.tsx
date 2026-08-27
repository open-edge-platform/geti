// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Heading, IllustratedMessage, View } from '@geti-ui/ui';
import { NotFound } from '@geti-ui/ui/icons';
import { isObject, isString } from 'lodash-es';
import { useTranslation } from 'react-i18next';
import { isRouteErrorResponse, useRouteError } from 'react-router-dom';

import { paths } from '../../constants/paths';
import { redirectTo } from '../utils';

const useErrorMessage = () => {
    const { t } = useTranslation();
    const error = useRouteError();

    if (isRouteErrorResponse(error)) {
        if (error.status === 400) {
            return t('errorPage.badRequest');
        }

        if (error.status === 403) {
            return t('errorPage.forbidden');
        }

        if (error.status === 404) {
            return t('errorPage.notFound');
        }

        if (error.status === 401) {
            return t('errorPage.unauthorized');
        }

        if (error.status === 500) {
            return t('errorPage.internalServerError');
        }

        if (error.status === 503) {
            return t('errorPage.serviceUnavailable');
        }
    }

    if (error instanceof TypeError) {
        return error.message;
    }

    if (isObject(error) && 'detail' in error && isString(error.detail)) {
        return error.detail;
    }

    return t('errorPage.unknown');
};

export const ErrorPage = () => {
    const { t } = useTranslation();
    const message = useErrorMessage();

    return (
        <View height={'100vh'}>
            <IllustratedMessage>
                <NotFound />
                <Heading>{message}</Heading>

                <Button
                    variant={'accent'}
                    marginTop={'size-200'}
                    onPress={() => {
                        redirectTo(paths.root({}));
                    }}
                >
                    {t('errorPage.backToHome')}
                </Button>
            </IllustratedMessage>
        </View>
    );
};
