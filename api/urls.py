from api import views as api_views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    # Authentication Endpoints
    path("user/token/", api_views.MyTokenObtainPairView.as_view()),
    path("user/token/refresh/", TokenRefreshView.as_view()),
    path("user/register/", api_views.RegisterView.as_view()),
    path("user/password-reset/<email>/", api_views.PasswordResetEmailVerifyAPIView.as_view()),
    path("user/password-change/", api_views.PasswordChangeAPIView.as_view()),
    path("user/change-password/", api_views.ChangePasswordAPIView.as_view()),

    # Core Endpoints
    path("cart/all/<cart_id>/", api_views.CartOwnAPIView.as_view()),
    path("course/category/", api_views.CategoryListAPIView.as_view()),
    path("course/course-list/", api_views.CourseListAPIView.as_view()),
    path("course/best-courses/", api_views.BestCoursesListAPIView.as_view()),
    path("course/course-detail/<slug>/", api_views.CourseDetailAPIView.as_view()),
    path("course/cart/", api_views.CartAPIView.as_view()),
    path("course/cart-list/<cart_id>/", api_views.CartListAPIView.as_view()),
    path("course/cart-item-delete/<cart_id>/<item_id>", api_views.CartItemDeleteAPIView.as_view()),
    path("course/search/", api_views.SearchCourseAPIView.as_view()),
    path("cart/stats/<cart_id>/", api_views.CartStatsAPIView.as_view()),
    path("order/create-order/", api_views.CreateOrderAPIView.as_view()),
    path("order/checkout/<oid>/", api_views.CheckOutAPIView.as_view()),
    path("order/coupon/", api_views.CouponApplyAPIView.as_view()),
    path("payment/stripe-checkout/<order_oid>/", api_views.StripeCheckoutAPIView.as_view()),
    path("payment/payment-success/", api_views.PaymentSuccessAPIView.as_view()),

    # Students API Endpoints
    path('student/enrolled-courses/', api_views.EnrolledCoursesAPIView.as_view()),
    path('student/summary/', api_views.StudentSummaryAPIViewNoIdPass.as_view()),
    path('student/course-detail/<enrollment_id>/', api_views.StudentCourseDetailAPIView.as_view()),
    path('student/course-completed/', api_views.StudentCourseCompletedCreateAPIView.as_view()),
    path('student/course-note/<enrollment_id>/', api_views.StudentNoteCreateAPIView.as_view()),
    path('student/course-note-detail/<enrollment_id>/<note_id>/', api_views.StudentNoteDetailAPIView.as_view()),
    path('student/rate-course/', api_views.StudentRateCourseCreateAPIView.as_view()),
    path('student/review-detail/<review_id>/', api_views.StudentRateCourseUpdateAPIView.as_view()),
    path('student/wishlist/', api_views.StudentWishListListCreateAPIView.as_view()),
    path('student/question-answer-list-create/<course_id>/', api_views.QuestionAndAnswerListAPIView.as_view()),
    path('student/question-answer-message-create/', api_views.QuestionAnswerMessageSendAPIView.as_view()),

]



