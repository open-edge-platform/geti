// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Header as SpectrumHeader, View } from '@adobe/react-spectrum';
import { ApiReferenceReact } from '@scalar/api-reference-react';
import { Link } from 'react-router-dom';

import { ReactComponent as Logo } from '../../assets/geti.svg';

import classes from './rest-api-specs.module.scss';

import '@scalar/api-reference-react/style.css';

import { paths } from '../../core/services/routes';

const Header = () => {
    return (
        <SpectrumHeader UNSAFE_className={classes.header}>
            <View padding={'size-200'}>
                <Link to={paths.root({})}>
                    <Logo />
                </Link>
            </View>
        </SpectrumHeader>
    );
};

export const RestApiSpecs = () => {
    return (
        <Flex direction={'column'} UNSAFE_className={classes.container} height={'100vh'}>
            <Header />
            <View flex={1} minHeight={0} overflow={'hidden auto'}>
                <ApiReferenceReact
                    configuration={{
                        spec: {
                            // to generate the openapi-spec.json file, run the following command:
                            // npm run build:rest-openapi-spec
                            url: '/openapi-spec.json',
                        },
                        layout: 'modern',
                        showSidebar: true,
                        hideModels: true,
                        hideClientButton: true,
                        hideDarkModeToggle: true,
                        metaData: {
                            title: 'REST API specification | Intel Geti™',
                        },
                        servers: [{ url: `/api/v1`, description: 'Geti - self hosted' }],
                        forceDarkModeState: 'dark',
                    }}
                />
            </View>
        </Flex>
    );
};
