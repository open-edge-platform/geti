// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Item, Key, Menu, MenuTrigger } from '@adobe/react-spectrum';

import { JointConnection } from '../../../../../assets/icons';
import { RegionOfInterest } from '../../../../../core/annotations/annotation.interface';
import { Button } from '../../../../../shared/components/button/button.component';
import { TemplateState } from '../util';
import { animalPose } from './animal-pose.template';
import { humanFace } from './human-face.template';
import { humanPose } from './human-pose.template';
import { formatTemplate, RawStructure } from './utils';

interface TemplatesProps {
    roi: RegionOfInterest;
    onAction: (template: TemplateState) => void;
}

export enum TemplatePose {
    HumanPose = 'Human pose',
    HumanFace = 'Human face',
    AnimalPose = 'Animal pose',
}

const templateMapper: Record<TemplatePose, RawStructure> = {
    [TemplatePose.HumanPose]: humanPose,
    [TemplatePose.HumanFace]: humanFace,
    [TemplatePose.AnimalPose]: animalPose,
};

export const Templates = ({ roi, onAction }: TemplatesProps) => {
    const handleAction = (key: Key) => {
        const templateKey = key as TemplatePose;
        const rawTemplate = templateMapper[templateKey];

        onAction(formatTemplate(rawTemplate, roi));
    };

    return (
        <MenuTrigger aria-label='templates menu'>
            <Button variant={'secondary'} maxWidth={'size-3000'} aria-label='templates list'>
                <Flex gap={'size-75'} alignItems={'center'}>
                    <JointConnection />
                    Templates
                </Flex>
            </Button>
            <Menu onAction={handleAction}>
                {Object.keys(templateMapper).map((name) => (
                    <Item key={name} textValue={name}>
                        {name}
                    </Item>
                ))}
            </Menu>
        </MenuTrigger>
    );
};
