// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useMutation } from '@tanstack/react-query';

export const useLogoutMutation = () => {
    const { authService } = useApplicationServices();

    return useMutation({ mutationFn: authService.logout });
};
