// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
