// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { createContext, ReactNode, useContext, useMemo } from 'react';

import { MissingProviderError } from '../../shared/missing-provider-error';
import { ApplicationServices } from './application-services.interface';
import { instance as defaultAxiosInstance } from './axios-instance';
import { getApiServices } from './get-api-services';
import { getInMemoryServices } from './get-in-memory-services';
import { useApiRouter } from './use-api-router.hook';

export type ApplicationServicesContextProps = ApplicationServices;

interface ApplicationServicesProviderProps extends Partial<ApplicationServicesContextProps> {
    children: ReactNode;
    useInMemoryEnvironment: boolean;
}

const ApplicationServiceContext = createContext<ApplicationServicesContextProps | undefined>(undefined);

// The ApplicationServicesProvider (should) hosts all services we use in our application
// this allows us to have one place where we can configure the app to use real apis,
// or to use an in memory service instead.
// Additionally, we may use this in our tests to overwrite a service's behavior, for example:
//
// render(
//     <ApplicationServicesProvider mediaService={myCustomMediaService}>
//         <YourComponentUsingMediaService />
//     </ApplicationServicesProvider>
// )
export const ApplicationServicesProvider = ({
    children,
    useInMemoryEnvironment = false,
    ...mockedServices
}: ApplicationServicesProviderProps): JSX.Element => {
    const router = useApiRouter();

    const services = useMemo((): ApplicationServicesContextProps => {
        const serviceConfiguration = { instance: defaultAxiosInstance, router };

        if (useInMemoryEnvironment) {
            return getInMemoryServices(serviceConfiguration);
        }

        return getApiServices(serviceConfiguration);
    }, [useInMemoryEnvironment, router]);

    // We overwrite any services that were explicitly passed in to the ApplicationServiceProvider
    // this allows us to overwrite the services' behavior in our tests
    const value = { ...services, ...mockedServices };

    return <ApplicationServiceContext.Provider value={value}>{children}</ApplicationServiceContext.Provider>;
};

export const useApplicationServices = (): ApplicationServicesContextProps => {
    const context = useContext(ApplicationServiceContext);

    if (context === undefined) {
        throw new MissingProviderError('useApplicationServices', 'ApplicationServiceProvider');
    }

    return context;
};
