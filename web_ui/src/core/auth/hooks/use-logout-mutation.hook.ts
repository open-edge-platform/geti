// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMutation } from '@tanstack/react-query';

import { useApplicationServices } from '../../services/application-services-provider.component';

export const useLogoutMutation = () => {
    const { authService } = useApplicationServices();

    return useMutation({ mutationFn: authService.logout });
};
