// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import * as yup from 'yup';

import { AccountStatus } from '../../../core/organizations/organizations.interface';

export const MAX_NUMBER_OF_CHARACTERS = 100;

const EMAIL_REGEX =
    // eslint-disable-next-line max-len
    /(?=^.{5,64}$)^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$/;

export const validateUserEmail = <T extends { email: string }>(email: string, users: T[]) =>
    yup.object({
        email: yup
            .string()
            .trim()
            .email('Invalid email format')
            .test('unique', `User with ${email} already exists`, (emailItem) => {
                if (emailItem) {
                    return !users.map((user) => user.email.toLocaleLowerCase()).includes(emailItem.toLocaleLowerCase());
                }

                return true;
            }),
    });

yup.addMethod(yup.string, 'email', function validateEmail(message) {
    return this.matches(EMAIL_REGEX, {
        message,
        name: 'email',
        excludeEmptyString: true,
    });
});

export const validateEmail = yup.string().email();

const STATUSES_FLOW: Record<AccountStatus, AccountStatus[]> = {
    [AccountStatus.INVITED]: [AccountStatus.ACTIVATED, AccountStatus.DELETED],
    [AccountStatus.ACTIVATED]: [AccountStatus.SUSPENDED, AccountStatus.DELETED],
    [AccountStatus.SUSPENDED]: [AccountStatus.ACTIVATED, AccountStatus.DELETED],
    [AccountStatus.DELETED]: [],
    [AccountStatus.REQUESTED_ACCESS]: [AccountStatus.ACTIVATED, AccountStatus.DELETED],
};

export const checkStatusFlowValidity = (from: AccountStatus, to: AccountStatus): boolean => {
    const validStatuses = STATUSES_FLOW[from];
    return validStatuses.includes(to);
};
