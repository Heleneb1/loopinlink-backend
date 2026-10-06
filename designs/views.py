from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from designs.utils import process_image, validate_image_file

from .models import Design, DesignImage
from .serializers import DesignSerializer


class DesignViewSet(viewsets.ModelViewSet):
    queryset = Design.objects.all()
    serializer_class = DesignSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        return Design.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        design = self.get_object()
        user = request.user

        if not user.is_staff:
            return Response(
                {"detail": "Action interdite : vous ne pouvez pas supprimer un design."},
                status=status.HTTP_403_FORBIDDEN,
            )

        design.delete()
        return Response(
            {"detail": "Design supprimé avec succès."},
            status=status.HTTP_204_NO_CONTENT,
        )


    @action(
        detail=False,
        methods=['get'],
        url_path='templates',
        permission_classes=[AllowAny]
    )
    def get_template_designs(self, request):
        templates = Design.objects.filter(is_template=True)
        serializer = self.get_serializer(
            templates, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['get'],
        url_path='template',
        permission_classes=[AllowAny]
    )
    def get_template(self, request, pk=None):
        try:
            template = Design.objects.get(pk=pk, is_template=True)
        except Design.DoesNotExist:
            return Response(
                {'detail': 'Template non trouvé.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(template, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = request.user
        design_type = request.data.get('type')

        if not design_type:
            return Response(
                {'detail': 'Le type du design est obligatoire.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_template = request.data.get('is_template', False)
        if isinstance(is_template, str):
            is_template = is_template.lower() == 'true'

        instance = None
        if not is_template:
            instance = Design.objects.filter(
                user=user, type=design_type, is_template=False
            ).first()

        # La limite ne s'applique qu'à une vraie création, pas à une mise à jour
        if not instance and not is_template:
            limit = None if user.is_superuser else (3 if user.is_staff else 1)
            design_count = Design.objects.filter(
                user=user, type=design_type, is_template=False
            ).count()

            if limit is not None and design_count >= limit:
                return Response(
                    {'detail': f'Limite atteinte : {limit} design(s) max pour "{design_type}".'},
                    status=status.HTTP_403_FORBIDDEN
                )

        if is_template and not user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Seuls les utilisateurs staff peuvent créer des templates."
            )
        # Valider tous les fichiers AVANT de toucher au serializer ou à la base
        for key, file in request.FILES.items():
            if key == 'preview_image':
                continue
            error = validate_image_file(file)
            if error:
                return Response({'detail': f'{key}: {error}'}, status=status.HTTP_400_BAD_REQUEST)

        # Nettoyer l'ancien preview_image physique avant réassignation, si mise à jour
        if instance and instance.preview_image and 'preview_image' in request.FILES:
            instance.preview_image.delete(save=False)

        if instance:
            serializer = self.get_serializer(
                instance, data=request.data, partial=True,
                context={'request': request},
            )
            status_code = status.HTTP_200_OK
        else:
            serializer = self.get_serializer(
                data=request.data, context={'request': request}
            )
            status_code = status.HTTP_201_CREATED

        serializer.is_valid(raise_exception=True)
        print("🔥 AVANT SERIALIZER.SAVE", flush=True)
        design = serializer.save(user=user, is_template=is_template)
        print("🔥 APRÈS SERIALIZER.SAVE", flush=True)

        # On repart d'une base propre : on retire les anciennes images liées
        # avant de réenregistrer celles envoyées dans cette requête.
        design.designimage_set.all().delete()

        for key, file in request.FILES.items():
            if key == 'preview_image':
                continue

            element_id = key.replace('file_', '')
            processed_file = process_image(file)

            DesignImage.objects.create(
                design=design,
                file=processed_file,
                element_id=element_id,
                type=design_type,
            )
        return Response(
            self.get_serializer(design, context={'request': request}).data,
            status=status_code,
        )

    @action(detail=False, methods=['post'], url_path='upload-image')
    def upload_image(self, request):
        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'Aucune image fournie.'}, status=status.HTTP_400_BAD_REQUEST)

        error = validate_image_file(image)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        processed_image = process_image(image)
        from django.core.files.storage import default_storage
        name = default_storage.save(f'designs/{image.name}', processed_image)
        url = request.build_absolute_uri(f'/media/{name}')

        return Response({'image_url': url}, status=status.HTTP_200_OK)

