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
