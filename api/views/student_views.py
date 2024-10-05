import logging

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from api import models as api_models
from api import serializer as api_serializer
from ..models import EnrolledCourse
from ..serializer import EnrolledCourseSerializer
from ..utils import User, get_user_from_request


class StudentSummaryAPIView(generics.ListAPIView):
    serializer_class = api_serializer.StudentSummarySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = User.objects.get(id=user_id)

        total_courses = api_models.EnrolledCourse.objects.filter(user=user).count()
        completed_lessons = api_models.CompletedLesson.objects.filter(user=user).count()
        achieved_certificates = api_models.Certificate.objects.filter(user=user).count()

        return [{
            'total_courses': total_courses,
            'completed_lessons': completed_lessons,
            'achieved_certificates': achieved_certificates,
        }]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StudentSummaryAPIViewNoIdPass(generics.ListAPIView):
    serializer_class = api_serializer.StudentSummarySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_user_from_request(self.request)
        if not user:
            return []

        total_courses = api_models.EnrolledCourse.objects.filter(user=user).count()
        completed_lessons = api_models.CompletedLesson.objects.filter(user=user).count()
        achieved_certificates = api_models.Certificate.objects.filter(user=user).count()
        enrolled_course_ids = list(
            api_models.EnrolledCourse.objects.filter(user=user).values_list('course_id', flat=True))
        wishlist_course_id = list(
            api_models.WishList.objects.filter(user=user).values_list('course_id', flat=True)
        )

        return [{
            'total_courses': total_courses,
            'completed_lessons': completed_lessons,
            'achieved_certificates': achieved_certificates,
            'enrolled_course_ids': enrolled_course_ids,
            'wishlist_course_id': wishlist_course_id
        }]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StudentCourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.EnrolledCourseSerializer
    permission_classes = [AllowAny]
    lookup_field = 'enrollment_id'

    def get_object(self):
        user = get_user_from_request(self.request)
        enrollment_id = self.kwargs['enrollment_id']

        logging.debug(f"User: {user}")
        logging.debug(f"Enrollment ID: {enrollment_id}")

        if not user or not enrollment_id:
            return []
        else:
            return api_models.EnrolledCourse.objects.get(user=user, enrollment_id=enrollment_id)


class StudentCourseCompletedCreateAPIView(generics.CreateAPIView):
    """
    Payload:
    {
        "course_id": 4,
        "variant_item_id": 767990
    }
    """

    serializer_class = api_serializer.CompletedLessonSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        course_id = request.data['course_id']
        variant_item_id = request.data['variant_item_id']

        course = api_models.Course.objects.get(id=course_id)
        variant_item = api_models.VariantItem.objects.get(variant_item_id=variant_item_id)

        completed_lessons = api_models.CompletedLesson.objects.filter(user=user, course=course,
                                                                      variant_item=variant_item).first()

        if completed_lessons:
            completed_lessons.delete()
            return Response({'message': 'Lesson not completed'}, status=status.HTTP_201_CREATED)

        else:
            api_models.CompletedLesson.objects.create(user=user, course=course, variant_item=variant_item)
            return Response({'message': 'Lesson completed'}, status=status.HTTP_201_CREATED)


class StudentNoteCreateAPIView(generics.ListCreateAPIView):
    """
    Payload to be sent:
    {
      "enrollment_id": 691623,
      "title": "A new Note",
      "note":  "It is a long established
                fact that a reader will be distracted
                by the readable content of a page when
                looking at its layout. The point of
                using Lorem Ipsum is that it has a more-or
                -less normal distribution of letters,",
    }
    """

    serializer_class = api_serializer.NoteSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_user_from_request(self.request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        enrollment_id = self.kwargs['enrollment_id']
        enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)

        return api_models.Note.objects.filter(user=user, course=enrolled.course)

    def create(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        enrollment_id = request.data['enrollment_id']
        title = request.data['title']
        note = request.data['note']

        enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)

        api_models.Note.objects.create(user=user, course=enrolled.course, note=note, title=title)

        return Response({'message': 'Note created successfully'}, status.HTTP_201_CREATED)


class StudentNoteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """This endpoint lets update, get or delete a particular note:
    PUT:
    {
     "enrollment_id": 691623,
     "title": "A new Note PUT",
     "note":  "The note"
    }
    PATCH:
    {
     "enrollment_id": 691623,
     "title": "A new Note PUT PATCH"
     "note":  "The note"
    }
"""
    serializer_class = api_serializer.NoteSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return api_models.Note.objects.all()

    def get_object(self):
        user = get_user_from_request(self.request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        enrollment_id = self.kwargs['enrollment_id']
        note_id = self.kwargs['note_id']

        enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)
        logging.debug(f'Note id is: {note_id}')
        note = api_models.Note.objects.get(user=user, course=enrolled.course, note_id=note_id)

        return note


class StudentRateCourseCreateAPIView(generics.CreateAPIView):
    """
    PAYLOAD
    {
    "course_id": 564235,
    "rating": 4,
    "review": "This is a great course!!",
    }
    OPTIONAL: "active": true
    """
    serializer_class = api_serializer.ReviewSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user = get_user_from_request(self.request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        course_id = request.data['course_id']
        rating = request.data['rating']
        review = request.data['review']
        # active = request.data['active']

        course = api_models.Course.objects.get(course_id=course_id)

        if api_models.Review.objects.filter(user=user, course=course).exists():
            return Response({'icon': 'warning', 'message': 'You have already reviewed this course'})

        # Add active=active
        api_models.Review.objects.create(user=user, course=course, review=review, rating=rating, active=True)

        return Response({'icon': 'success', "message": "Review created successfully"})


class StudentRateCourseUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializer.ReviewSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user = get_user_from_request(self.request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        review_id = self.kwargs['review_id']

        return api_models.Review.objects.get(id=review_id, user=user)


class StudentWishListListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializer.WishlistSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_user_from_request(self.request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        return api_models.WishList.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        user = get_user_from_request(self.request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        course_id = request.data['course_id']
        course = api_models.Course.objects.get(id=course_id)

        wishlist = api_models.WishList.objects.filter(user=user, course=course).first()

        if wishlist:
            wishlist.delete()
            return Response({'icon': 'warning', 'message': 'Deleted from wishlist'}, status=status.HTTP_200_OK)
        else:
            api_models.WishList.objects.create(
                user=user,
                course=course
            )
            return Response({'icon': 'success', 'message': 'Added to wishlist'}, status=status.HTTP_201_CREATED)


class QuestionAndAnswerListAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializer.QuestionAnswerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course = api_models.Course.objects.get(id=course_id)
        return api_models.QuestionAnswer.objects.filter(course=course)

    def create(self, request, *args, **kwargs):
        user = get_user_from_request(self.request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        course_id = request.data['course_id']
        title = request.data['title']
        message = request.data['message']

        course = api_models.Course.objects.get(id=course_id)

        question = api_models.QuestionAnswer.objects.create(course=course, user=user, title=title)

        api_models.QuestionAnswerMessage.objects.create(
            course=course,
            user=user,
            message=message,
            question=question
        )

        return Response({'message': 'Group conversation started'}, status=status.HTTP_201_CREATED)


class QuestionAnswerMessageSendAPIView(generics.CreateAPIView):
    """
    PAYLOAD:
    {
    "course_id": 4,
    "qa_id": 379665,
    "message": "You have to run your server from the console"
    }
    """

    serializer_class = api_serializer.QuestionAnswerMessageSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user = get_user_from_request(self.request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        course_id = request.data['course_id']
        qa_id = request.data['qa_id']
        message = request.data['message']

        course = api_models.Course.objects.get(id=course_id)
        question = api_models.QuestionAnswer.objects.get(qa_id=qa_id)

        api_models.QuestionAnswerMessage.objects.create(course=course, user=user, message=message, question=question)

        question_serializer = api_serializer.QuestionAnswerSerializer(question)
        return Response({"message": "Message sent", "question": question_serializer.data})


class EnrolledCoursesAPIView(generics.ListAPIView):
    serializer_class = EnrolledCourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_user_from_request(self.request)
        if user:
            return EnrolledCourse.objects.filter(user=user)
        else:
            return EnrolledCourse.objects.none()
