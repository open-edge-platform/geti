// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Header as SpectrumHeader, View } from '@geti/ui';
import { ApiReferenceReact } from '@scalar/api-reference-react';
import { Link } from 'react-router-dom';

import { ReactComponent as Logo } from '../../assets/geti.svg';

import classes from './rest-api-specs.module.scss';

import '@scalar/api-reference-react/style.css';

import { paths } from '@geti/core/src/services/routes';

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
