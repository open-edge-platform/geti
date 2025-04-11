// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Text } from '@adobe/react-spectrum';

import { DateCell } from '../../../../shared/components/table/date-cell/date-cell.component';

interface LastLoginCellProps {
    id: string;
    lastSuccessfulLogin: string | null;
    direction?: 'column' | 'row';
}

export const LastLoginCell = ({ id, lastSuccessfulLogin, direction = 'column' }: LastLoginCellProps): JSX.Element => {
    if (lastSuccessfulLogin === null) {
        return <Text id={id}>N/A</Text>;
    }

    return <DateCell id={id} date={lastSuccessfulLogin} direction={direction} />;
};
