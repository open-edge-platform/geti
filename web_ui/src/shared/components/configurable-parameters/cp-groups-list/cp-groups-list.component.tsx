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

import { View } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { ANIMATION_PARAMETERS } from '../../../animation-parameters/animation-parameters';
import { ConfigParameterItemProp, ConfigurableParametersGroups } from '../configurable-parameters.interface';
import { CPGroupItem } from '../cp-group-item/cp-group-item.component';

interface CPGroupsListProps extends ConfigParameterItemProp {
    groups: ConfigurableParametersGroups[];
}

export const CPGroupsList = ({ groups, updateParameter }: CPGroupsListProps): JSX.Element => {
    const isExpandable = groups.length > 1;
    return (
        <View>
            <AnimatePresence mode='wait'>
                {groups.map((group, index) => (
                    <motion.div
                        variants={ANIMATION_PARAMETERS.ANIMATE_LIST}
                        initial={'hidden'}
                        animate={'visible'}
                        exit={'hidden'}
                        layoutId={group.id}
                        custom={index}
                        key={group.id}
                    >
                        <CPGroupItem group={group} isExpandable={isExpandable} updateParameter={updateParameter} />
                    </motion.div>
                ))}
            </AnimatePresence>
        </View>
    );
};
