// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { MediaProvider } from '../media/providers/media-provider.component';
import { useNextMediaItemWithImage } from './hooks/use-next-media-item-with-image.hook';
import { AnnotationToolProvider } from './providers/annotation-tool-provider/annotation-tool-provider.component';
import { AnnotatorProvider, MediaItemProvider } from './providers/annotator-provider/annotator-provider.component';
import { DatasetProvider } from './providers/dataset-provider/dataset-provider.component';
import { RegionOfInterestProvider } from './providers/region-of-interest-provider/region-of-interest-provider.component';
import { SelectedMediaItemProvider } from './providers/selected-media-item-provider/selected-media-item-provider.component';
import { TaskProvider } from './providers/task-provider/task-provider.component';
import { SyncZoomState, SyncZoomTarget } from './zoom/sync-zoom-state.component';
import { ZoomProvider } from './zoom/zoom-provider.component';

// This hook is called in an empty component so that any of its state updates won't
// trigger rerenders of the component using it, this makes it so that we can preload
// the image of the next media item while not affecting any other components
const PreLoadImageOfNextMediaItem = () => {
    useNextMediaItemWithImage();

    return <></>;
};

interface AnnotatorProps {
    children: ReactNode;
}

export const Annotator = ({ children }: AnnotatorProps): JSX.Element => {
    return (
        <MediaProvider>
            <ZoomProvider>
                <TaskProvider>
                    <DatasetProvider>
                        <SelectedMediaItemProvider>
                            <SyncZoomState />
                            <SyncZoomTarget />
                            <AnnotatorProvider>
                                <RegionOfInterestProvider>
                                    <MediaItemProvider>
                                        <PreLoadImageOfNextMediaItem />
                                        <AnnotationToolProvider>{children}</AnnotationToolProvider>
                                    </MediaItemProvider>
                                </RegionOfInterestProvider>
                            </AnnotatorProvider>
                        </SelectedMediaItemProvider>
                    </DatasetProvider>
                </TaskProvider>
            </ZoomProvider>
        </MediaProvider>
    );
};
