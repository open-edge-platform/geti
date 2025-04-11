from geti_types import (
    ID,
    ImageIdentifier,
    MediaIdentifierEntity,
    NullMediaIdentifier,
    VideoFrameIdentifier,
    VideoIdentifier,
)


class TestMediaIdentifiers:
    def test_null_media_identifier_equality(self) -> None:
        """
        <b>Description:</b>
        Test whether the all NullMediaIdentifier() entities __hash__ and __eq__ are equal

        <b>Input data:</b>
        NullMediaIdentifiers

        <b>Expected results:</b>
        Test passes if each created NullMediaIdentifier is equal to each other

        <b>Steps</b>
        1. Add 10 NullMediaIdentifier to set
        2. Check that length of set is equal to 1
        """
        null_media_identifiers = set()
        for _ in range(10):
            identifier = NullMediaIdentifier()
            null_media_identifiers.add(identifier)
            assert identifier in null_media_identifiers
        assert len(null_media_identifiers) == 1, "Expected one NullMediaIdentifier in null_media_identifiers"

    def test_image_media_identifier_equality(self) -> None:
        """
        <b>Description:</b>
        Test whether the ImageIdentifier hashes based on the ID of the image

        <b>Input data:</b>
        ID's created from integers 0 to 5

        <b>Expected results:</b>
        Test passes if both sets of created ImageIdentifiers are identical to each other

        <b>Steps</b>
        1. Create first set of Identifiers
        2. Create second set of Identifiers
        3. Compare Identifiers
        """
        image_media_identifiers = set()
        # Produce 5 unique identifiers
        for i in range(5):
            identifier = ImageIdentifier(image_id=ID(str(i)))
            image_media_identifiers.add(identifier)
            assert identifier in image_media_identifiers
        # Produce yet again, 5 unique. They should be the same as the first generated 5
        for i in range(5):
            identifier = ImageIdentifier(image_id=ID(str(i)))
            image_media_identifiers.add(identifier)
            assert identifier in image_media_identifiers
        assert len(image_media_identifiers) == 5, "Expected 5 ImageIdentifier in image_media_identifiers"

    def test_video_media_identifier_equality(self) -> None:
        """
        <b>Description:</b>
        Test whether the VideoIdentifier hashes based on the ID of the video

        <b>Input data:</b>
        ID's created from integers 0 to 5

        <b>Expected results:</b>
        Test passes if both sets of created VideoIdentifier are identical to each other

        <b>Steps</b>
        1. Create first set of Identifiers
        2. Create second set of Identifiers
        3. Compare Identifiers
        """
        video_media_identifiers = set()
        # Produce 5 unique identifiers
        for i in range(5):
            identifier = VideoIdentifier(video_id=ID(str(i)))
            video_media_identifiers.add(identifier)
            assert identifier in video_media_identifiers
        # Produce yet again, 5 unique. They should be the same as the first generated 5
        for i in range(5):
            identifier = VideoIdentifier(video_id=ID(str(i)))
            video_media_identifiers.add(identifier)
            assert identifier in video_media_identifiers
        assert len(video_media_identifiers) == 5, "Expected 5 VideoIdentifier in image_media_identifiers"

    def test_video_frame_identifier_equality(self) -> None:
        """
        <b>Description:</b>
        Test whether the VideoFrameIdentifier hashes based on the ID and frame index of the video

        <b>Input data:</b>
        ID's created from integers 0 to 5

        <b>Expected results:</b>
        Test passes if 9 unique VideoFrameIdentifiers are created

        <b>Steps</b>
        1. Create first set of Identifiers while changing frame_index
        2. Create second set of Identifiers while keeping frame_index at 0
        3. Check that 9 unique VideoFrameIdentifiers were created
        """
        video_frame_identifiers = set()
        # Produce 5 unique identifiers
        for i in range(5):
            identifier = VideoFrameIdentifier(video_id=ID(str(i)), frame_index=i)
            video_frame_identifiers.add(identifier)
            assert identifier in video_frame_identifiers
        # Produce yet again, 5 unique. They should be the same as the first generated 5
        for i in range(5):
            identifier = VideoFrameIdentifier(video_id=ID(str(i)), frame_index=0)
            video_frame_identifiers.add(identifier)
            assert identifier in video_frame_identifiers
        assert len(video_frame_identifiers) == 9, "Expected nine NullMediaIdentifier in video_frame_identifiers"

    def test_mixed(self) -> None:
        """
        <b>Description:</b>
        Test whether the media identifiers hash to unique values, and their equality is guaranteed

        <b>Input data:</b>
        Various random ObjectID's

        <b>Expected results:</b>
        Test passes if each MediaIdentifier hashes to unique values

        <b>Steps</b>
        1. Create Object ID's
        2. Create various MediaIdentifiers
        3. Check that four Identifiers were added to the set
        """
        mixed: set[MediaIdentifierEntity] = set()

        id1 = ID()
        id2 = ID()
        id3 = ID()

        # Add four types of identifiers
        mixed.add(VideoFrameIdentifier(video_id=ID(id1), frame_index=0))
        mixed.add(VideoIdentifier(video_id=ID(id2)))
        mixed.add(ImageIdentifier(image_id=ID(id3)))
        mixed.add(NullMediaIdentifier())

        # Add identical entities again
        mixed.add(VideoFrameIdentifier(video_id=ID(id1), frame_index=0))
        mixed.add(VideoIdentifier(video_id=ID(id2)))
        mixed.add(ImageIdentifier(image_id=ID(id3)))
        mixed.add(NullMediaIdentifier())

        assert len(mixed) == 4, "Expected four Identifiers in mixed set"
