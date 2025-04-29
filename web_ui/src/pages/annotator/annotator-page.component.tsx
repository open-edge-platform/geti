// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AnnotatorLayout } from './annotator-layout.component';
import { Annotator } from './annotator.component';

const AnnotatorPage = () => {
    return (
        <Annotator>
            <AnnotatorLayout />
        </Annotator>
    );
};

export default AnnotatorPage;
