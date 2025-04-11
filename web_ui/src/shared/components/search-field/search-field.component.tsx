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

import { ComponentProps, forwardRef } from 'react';

import { SearchField as SpectrumSearchField } from '@adobe/react-spectrum';
import { TextFieldRef } from '@react-types/textfield';

type SearchFieldProps = Omit<ComponentProps<typeof SpectrumSearchField>, 'ref'>;

export const SearchField = forwardRef<TextFieldRef, SearchFieldProps>((props, ref): JSX.Element => {
    return <SpectrumSearchField {...props} ref={ref} />;
});
