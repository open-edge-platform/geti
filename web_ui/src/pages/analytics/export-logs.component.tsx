// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import {
    Button,
    ButtonGroup,
    Content,
    DateRangePicker,
    Dialog,
    DialogTrigger,
    Divider,
    Heading,
    Radio,
    RadioGroup,
    type RangeValue,
} from '@geti/ui';
import { DateValue, getLocalTimeZone, today } from '@internationalized/date';
import dayjs from 'dayjs';

import { useApplicationServices } from '../../core/services/application-services-provider.component';
import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { downloadFile, getDateTimeInISOAndUTCOffsetFormat, getDownloadNotificationMessage } from '../../shared/utils';
import { idMatchingFormat } from '../../test-utils/id-utils';
import { DownloadButton } from './download-button.component';

const NOW = today(getLocalTimeZone());
// TODO: ideally we want to set MIN_DATE to be date of the platform installation, but it's not possible atm
// workaround solution is to allow user to export logs from range of 3 months
const MIN_DATE = NOW.subtract({ days: 3 * 30 });

const INITIAL_DATES: RangeValue<DateValue> = {
    start: NOW.subtract({ days: 1 }),
    end: NOW,
};

export enum ExportAnalyticsType {
    METRICS = 'Metrics',
    TRACES = 'Traces',
    LOGS = 'Logs',
}

export type URLType = (startDate: string, endDate: string) => string;

export enum ExportAnalyticsSubTypes {
    APPLICATION = 'Application',
    SERVER = 'Server',
}

interface ExportAnalyticsDataProps {
    urls: URLType[];
    exportType: ExportAnalyticsType;
}

export const ExportAnalyticsData = ({ urls, exportType }: ExportAnalyticsDataProps): JSX.Element => {
    const { router } = useApplicationServices();
    const exportName = exportType.toLocaleLowerCase();
    const { addNotification } = useNotification();
    const [selectedExportSubType, setSelectedExportSubType] = useState<ExportAnalyticsSubTypes | undefined>(undefined);
    const shouldShowSubTypes = exportType !== ExportAnalyticsType.TRACES;

    const [datesRange, setDatesRange] = useState<RangeValue<DateValue>>(INITIAL_DATES);
    const { start, end } = datesRange;

    const areDatesValid =
        end.compare(NOW) <= 0 && end.compare(start) >= 0 && start.compare(MIN_DATE) >= 0 && start.compare(end) <= 0;

    const isExportButtonDisabled = !areDatesValid || (shouldShowSubTypes && selectedExportSubType === undefined);

    const handleSubTypeChange = (key: string) => {
        setSelectedExportSubType(key as ExportAnalyticsSubTypes);
    };

    const handleClose = (close: () => void) => () => {
        close();
        // NOTE: We add this timeout to set initial state when dialog is closed so the user does not see flashing input
        setTimeout(() => {
            setDatesRange(INITIAL_DATES);
            setSelectedExportSubType(undefined);
        }, 100);
    };

    const handleExport = (close: () => void) => () => {
        const [applicationUrl, serverUrl] = urls;
        let url = serverUrl;

        // Traces or application type
        if (selectedExportSubType === undefined || selectedExportSubType === ExportAnalyticsSubTypes.APPLICATION) {
            url = applicationUrl;
        }

        // Note: We need to send dates in ISO8601 format + UTC offset
        const startDateTime = getDateTimeInISOAndUTCOffsetFormat(dayjs(start.toString()).startOf('d'));
        const endDateTime = getDateTimeInISOAndUTCOffsetFormat(dayjs(end.toString()).endOf('d'));

        downloadFile(router.PREFIX(url(startDateTime, endDateTime)));

        addNotification({ message: getDownloadNotificationMessage(exportName), type: NOTIFICATION_TYPE.INFO });

        handleClose(close)();
    };

    const handleChangeDatesRange = (value: RangeValue<DateValue> | null) => {
        if (value === null) {
            return;
        }
        setDatesRange(value);
    };

    return (
        <DialogTrigger>
            <DownloadButton exportName={exportName} />
            {(close) => (
                <Dialog size={'M'}>
                    <Heading>Export {exportName}</Heading>
                    <Divider />
                    <Content>
                        <DateRangePicker
                            id={`dates-range-${idMatchingFormat(exportName)}-id`}
                            label={'Dates range'}
                            value={datesRange}
                            onChange={handleChangeDatesRange}
                            minValue={MIN_DATE}
                            maxValue={NOW}
                        />
                        {shouldShowSubTypes && (
                            <RadioGroup
                                aria-label={`${exportType} type`}
                                value={selectedExportSubType}
                                onChange={handleSubTypeChange}
                                marginTop={'size-200'}
                            >
                                <Radio value={ExportAnalyticsSubTypes.APPLICATION}>
                                    {ExportAnalyticsSubTypes.APPLICATION} {exportName}
                                </Radio>
                                <Radio value={ExportAnalyticsSubTypes.SERVER}>
                                    {ExportAnalyticsSubTypes.SERVER} {exportName}
                                </Radio>
                            </RadioGroup>
                        )}
                    </Content>
                    <ButtonGroup>
                        <Button variant={'secondary'} onPress={handleClose(close)}>
                            Close
                        </Button>
                        <Button variant={'accent'} onPress={handleExport(close)} isDisabled={isExportButtonDisabled}>
                            Export
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogTrigger>
    );
};
