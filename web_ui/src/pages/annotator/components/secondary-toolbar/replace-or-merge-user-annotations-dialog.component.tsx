// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ButtonGroup, Content, Dialog, Divider, Text } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';
import { Heading } from '@react-spectrum/text';

import { usePrediction } from '../../providers/prediction-provider/prediction-provider.component';

interface ReplaceOrMergeUserAnnotationsDialogProps {
    merge: () => void;
    replace: () => void;
    close: () => void;
}

export const ReplaceOrMergeUserAnnotationsDialog = ({
    merge,
    replace,
    close,
}: ReplaceOrMergeUserAnnotationsDialogProps): JSX.Element => {
    const { enableMergingPredictionsPredicate } = usePrediction();
    const hideMerge = !enableMergingPredictionsPredicate();

    const onMerge = () => {
        close();
        merge();
    };
    const onReplace = () => {
        close();
        replace();
    };

    return (
        <Dialog>
            <Heading>Replace {hideMerge ? '' : 'or merge '}annotations?</Heading>
            <Divider />
            <Content>
                {hideMerge ? (
                    <Text>
                        Do you want to replace your annotations with these accepted ones given by AI prediction?
                    </Text>
                ) : (
                    <Text>
                        Do you want to replace your annotations with these accepted ones given by AI prediction or merge
                        them as new ones?
                    </Text>
                )}
            </Content>
            <ButtonGroup>
                <Button variant='secondary' onPress={close} id='cancel-predictions'>
                    Cancel
                </Button>
                {hideMerge ? (
                    <></>
                ) : (
                    <Button variant='accent' onPress={onMerge} id='merge-predictions'>
                        Merge
                    </Button>
                )}
                <Button variant='accent' onPress={onReplace} id='replace-predictions'>
                    Replace
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};
