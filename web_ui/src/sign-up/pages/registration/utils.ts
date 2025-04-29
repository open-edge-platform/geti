// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PasswordState } from '../../../pages/user-management/users/add-member-popup/add-member-popup.interface';

export const handleErrorMessageState = (message: string) => {
    return (prevState: PasswordState): PasswordState => {
        let errorMsg = prevState.error;

        if (prevState.error) {
            errorMsg += '\n';
        }

        return {
            ...prevState,
            error: errorMsg + message,
        };
    };
};
