// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface UpdatePasswordDTO {
    uid: string;
    new_password: string;
    old_password: string;
}

export interface ForgotPasswordDTO {
    email: string;
}

export interface UserRegistrationDTO {
    first_name: string;
    second_name: string;
    token: string;
    password: string;
}

export interface ResetPasswordDTO {
    token: string;
    new_password: string;
}
