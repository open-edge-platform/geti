// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Content, Heading, IllustratedMessage } from '@geti/ui';
import { NotFound as NotFoundSpectrum } from '@geti/ui/icons';

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
