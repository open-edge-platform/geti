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
    const error = useRouteError();
    const { t } = useTranslation();

    if (isRouteErrorResponse(error)) {
        if (error.status === 400) {
            return t('common.serverCannotProcess');
        }

        if (error.status === 403) {
            return t('common.noPermission');
        }

        if (error.status === 404) {
            return t('common.notExist');
        }

        if (error.status === 401) {
            return t('common.notAuthorized');
        }

        if (error.status === 500) {
            return t('common.serverErrorGeneric');
        }

        if (error.status === 503) {
            return t('common.apiDown');
        }
    }

    if (error instanceof TypeError) {
        return error.message;
    }

    if (isObject(error) && 'detail' in error && isString(error.detail)) {
        return error.detail;
    }

    return t('common.unknownErrorGeneric');
};

export const ErrorPage = () => {
    const message = useErrorMessage();
    const { t } = useTranslation();

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
                    {t('common.goBackHome')}
                </Button>
            </IllustratedMessage>
        </View>
    );
};
