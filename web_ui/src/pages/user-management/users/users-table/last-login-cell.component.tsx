// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
