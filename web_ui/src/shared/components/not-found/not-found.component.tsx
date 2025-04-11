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

import { Content, Heading, IllustratedMessage } from '@adobe/react-spectrum';
import NotFoundSpectrum from '@spectrum-icons/illustrations/NotFound';

interface NotFoundProps {
    heading?: string;
    content?: string;
}

export const NotFound = ({ heading = 'No results', content = 'Try another search' }: NotFoundProps): JSX.Element => (
    <IllustratedMessage>
        <NotFoundSpectrum />
        <Heading>{heading}</Heading>
        <Content>{content}</Content>
    </IllustratedMessage>
);
