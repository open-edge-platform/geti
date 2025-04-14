// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, forwardRef } from 'react';

import { SearchField as SpectrumSearchField } from '@adobe/react-spectrum';
import { TextFieldRef } from '@react-types/textfield';

type SearchFieldProps = Omit<ComponentProps<typeof SpectrumSearchField>, 'ref'>;

export const SearchField = forwardRef<TextFieldRef, SearchFieldProps>((props, ref): JSX.Element => {
    return <SpectrumSearchField {...props} ref={ref} />;
});
