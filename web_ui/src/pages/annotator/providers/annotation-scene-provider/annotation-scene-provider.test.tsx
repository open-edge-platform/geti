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

import { useState } from 'react';

import { fireEvent, render, screen, within } from '@testing-library/react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { Label } from '../../../../core/labels/label.interface';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel, labels as mockLabels } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { AnnotationSceneProvider, useAnnotationScene } from './annotation-scene-provider.component';

describe('Annotation scene provider', (): void => {
    const labels: Label[] = [
        getMockedLabel({ id: 'card', color: '#00ff00', name: 'card', group: 'card-group', parentLabelId: null }),
        getMockedLabel({ id: 'black', color: '#00ffff', name: 'black', group: 'color', parentLabelId: 'card' }),
        getMockedLabel({ id: 'red', color: '#00ffff', name: 'red', group: 'color', parentLabelId: 'card' }),
    ];
    const annotations: Annotation[] = [
        {
            id: 'rect-1',
            labels: [labelFromUser(labels[0])],
            shape: { shapeType: ShapeType.Rect, x: 10, y: 10, width: 300, height: 300 },
            zIndex: 0,
            isSelected: false,
            isHidden: false,
            isLocked: false,
        },
        {
            id: 'rect-2',
            labels: [labelFromUser(labels[0])],
            shape: { shapeType: ShapeType.Rect, x: 410, y: 410, width: 300, height: 300 },
            zIndex: 1,
            isSelected: false,
            isHidden: false,
            isLocked: false,
        },
    ];

    const AnnotationList = () => {
        const scene = useAnnotationScene();

        return (
            <ul title='annotations'>
                {scene.annotations.map((annotation) => (
                    <li key={annotation.id}>
                        {annotation.id} - {annotation.labels.map(({ name }) => name).join(', ')}
                    </li>
                ))}
            </ul>
        );
    };

    const LabelsList = () => {
        const scene = useAnnotationScene();

        return (
            <ul title='labels'>
                {scene.labels.map((label) => (
                    <li key={label.id}>
                        {label.id} - {label.name}
                    </li>
                ))}
            </ul>
        );
    };

    it('keeps track of annotations and labels', (): void => {
        render(
            <AnnotationSceneProvider annotations={annotations} labels={labels}>
                <AnnotationList />
                <LabelsList />
            </AnnotationSceneProvider>
        );

        expect(within(screen.getByRole('list', { name: 'annotations' })).getAllByRole('listitem')).toHaveLength(2);
        expect(within(screen.getByRole('list', { name: 'labels' })).getAllByRole('listitem')).toHaveLength(3);
    });

    it('allows us to add a shape to the annotation scene', (): void => {
        const App = () => {
            const scene = useAnnotationScene();

            const onClick = () => {
                scene.addShapes([{ shapeType: ShapeType.Rect, x: 0, y: 0, width: 10, height: 10 }]);
            };

            return <button onClick={onClick}>Add shape</button>;
        };
        render(
            <AnnotationSceneProvider annotations={annotations} labels={labels}>
                <App />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        fireEvent.click(screen.getByRole('button'));
        expect(screen.getAllByRole('listitem')).toHaveLength(3);
    });

    it('allows us to add a shape with a label to the annotation scene', (): void => {
        const App = () => {
            const scene = useAnnotationScene();

            const onClick = () => {
                scene.addShapes([{ shapeType: ShapeType.Rect, x: 0, y: 0, width: 10, height: 10 }], [scene.labels[1]]);
            };

            return <button onClick={onClick}>Add shape</button>;
        };
        render(
            <AnnotationSceneProvider annotations={annotations} labels={labels}>
                <App />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        fireEvent.click(screen.getByRole('button'));
        expect(screen.getByText('- card, black', { exact: false })).toBeInTheDocument();
    });

    it('allows us to remove an annotation from the annotation scene', (): void => {
        const App = () => {
            const scene = useAnnotationScene();

            const onClick = () => {
                scene.removeAnnotations([annotations[0]]);
            };

            return <button onClick={onClick}>Add shape</button>;
        };
        render(
            <AnnotationSceneProvider annotations={annotations} labels={labels}>
                <App />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        fireEvent.click(screen.getByRole('button'));
        expect(screen.getAllByRole('listitem')).toHaveLength(1);
        expect(screen.queryByText(`${annotations[0].id} - ${labels[0].name}`)).not.toBeInTheDocument();
    });

    it('allows us to update an annotation from the annotation scene', (): void => {
        const App = () => {
            const scene = useAnnotationScene();

            const onClick = () => {
                scene.updateAnnotation({
                    ...annotations[0],
                    labels: [labelFromUser(labels[0]), labelFromUser(labels[1])],
                });
            };

            return <button onClick={onClick}>Add shape</button>;
        };
        render(
            <AnnotationSceneProvider annotations={annotations} labels={labels}>
                <App />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        fireEvent.click(screen.getByRole('button'));
        expect(screen.getByText(`${annotations[0].id} - ${labels[0].name}, ${labels[1].name}`)).toBeInTheDocument();
    });

    it('resets annotation state when initial annotations are changed', (): void => {
        const App = () => {
            const [initialAnnotations, setInitialAnnotations] = useState(annotations);

            const onClick = () => {
                setInitialAnnotations([annotations[0]]);
            };

            return (
                <>
                    <button onClick={onClick}>Change initial annotations</button>
                    <AnnotationSceneProvider annotations={initialAnnotations} labels={labels}>
                        <AnnotationList />
                        <LabelsList />
                    </AnnotationSceneProvider>
                </>
            );
        };
        render(<App />);

        expect(within(screen.getByRole('list', { name: 'annotations' })).getAllByRole('listitem')).toHaveLength(2);
        fireEvent.click(screen.getByRole('button'));
        expect(within(screen.getByRole('list', { name: 'annotations' })).getAllByRole('listitem')).toHaveLength(1);
    });

    // describe labeling annotations
    describe('labelling annotations', () => {
        describe('Adding labels', () => {
            const AddLabel = ({ label, annotationIds }: { label: Label; annotationIds: string[] }) => {
                const scene = useAnnotationScene();

                const onClick = () => {
                    scene.addLabel(label, annotationIds);
                };

                return <button onClick={onClick}>Add label</button>;
            };

            it('adds labels using label resolver', (): void => {
                const mockAnnotations: Annotation[] = [
                    getMockedAnnotation({
                        id: 'rect-1',
                        labels: [
                            labelFromUser(mockLabels[0]),
                            labelFromUser(mockLabels[1]),
                            labelFromUser(mockLabels[5]),
                            labelFromUser(mockLabels[10]),
                        ],
                    }),
                    getMockedAnnotation({
                        id: 'rect-2',
                        labels: [labelFromUser(mockLabels[0])],
                    }),
                ];

                render(
                    <AnnotationSceneProvider annotations={mockAnnotations} labels={mockLabels}>
                        <AddLabel label={mockLabels[3]} annotationIds={['rect-1']} />
                        <AnnotationList />
                    </AnnotationSceneProvider>
                );

                expect(screen.getByText(`${mockAnnotations[0].id} - card, black, ♠, 4`)).toBeInTheDocument();
                fireEvent.click(screen.getByRole('button'));
                expect(screen.getByText(`${mockAnnotations[0].id} - card, red, ♥, 4`)).toBeInTheDocument();
                expect(screen.getByText(`${mockAnnotations[1].id} - card`)).toBeInTheDocument();
            });
        });

        describe('Removing labels', () => {
            const RemoveLabel = ({ label, annotationIds }: { label: Label; annotationIds: string[] }) => {
                const scene = useAnnotationScene();

                const onClick = () => {
                    scene.removeLabels([label], annotationIds);
                };

                return <button onClick={onClick}>Add label</button>;
            };

            it('removes labels using label resolver', (): void => {
                const mockAnnotations: Annotation[] = [
                    getMockedAnnotation({
                        id: 'rect-1',
                        labels: [
                            labelFromUser(mockLabels[0]),
                            labelFromUser(mockLabels[1]),
                            labelFromUser(mockLabels[5]),
                            labelFromUser(mockLabels[10]),
                        ],
                    }),
                    getMockedAnnotation({
                        id: 'rect-2',
                        labels: [labelFromUser(mockLabels[0])],
                    }),
                ];

                render(
                    <AnnotationSceneProvider annotations={mockAnnotations} labels={mockLabels}>
                        <RemoveLabel label={mockLabels[1]} annotationIds={['rect-1']} />
                        <AnnotationList />
                    </AnnotationSceneProvider>
                );

                fireEvent.click(screen.getByRole('button'));
                expect(screen.getByText(`${mockAnnotations[0].id} - card, 4`)).toBeInTheDocument();
                expect(screen.getByText(`${mockAnnotations[1].id} - card`)).toBeInTheDocument();
            });
        });
    });
});
