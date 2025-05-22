// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@geti/ui';
import { AnimatePresence, motion } from 'framer-motion';

import {
    ConfigParameterItemProp,
    ConfigurableParametersGroups,
} from '../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { ANIMATION_PARAMETERS } from '../../../animation-parameters/animation-parameters';
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
